import hashlib
import logging
import os
import tempfile
import uuid
from math import ceil
from time import monotonic
from typing import FrozenSet, Optional, Set, Union

import aiohttp
from aiogram.types import FSInputFile, Message
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from access_control import parse_operator_ids


logger = logging.getLogger(__name__)
POLICY_URL = "https://upmini.app/documents/2026-09-21-v1.1/pdf/03-personal-data-policy.pdf"
FORM_EXPORT_COOLDOWN_SECONDS = 60
_last_export_at: dict[int, float] = {}


class FormResponseError(Exception):
    """Raised when the forms API cannot return a usable response payload."""


def _fingerprint(value: object) -> str:
    """Return a short pseudonymous reference for audit logs."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _audit_export(event: str, actor_id: Optional[int], form_id: Optional[str] = None, **fields) -> None:
    actor_ref = _fingerprint(actor_id) if actor_id is not None else "unknown"
    form_ref = _fingerprint(form_id) if form_id is not None else "none"
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info(
        "form_res_export event=%s actor_ref=%s form_ref=%s%s",
        event,
        actor_ref,
        form_ref,
        f" {details}" if details else "",
    )


def _normalize_form_id(value: str) -> str:
    if len(value) != 36:
        raise ValueError("invalid form id")
    normalized = str(uuid.UUID(value))
    if value.lower() != normalized:
        raise ValueError("invalid form id")
    return normalized


def _safe_excel_value(value):
    formatted = format_value_for_excel(value)
    if formatted.startswith(("=", "+", "-", "@")):
        return f"'{formatted}"
    return formatted


def _reserve_export(actor_id: int) -> int:
    """Apply a process-local cooldown before starting an expensive data export."""
    now = monotonic()
    previous = _last_export_at.get(actor_id)
    if previous is not None:
        remaining = FORM_EXPORT_COOLDOWN_SECONDS - (now - previous)
        if remaining > 0:
            return max(1, ceil(remaining))
    _last_export_at[actor_id] = now
    if len(_last_export_at) > 256:
        expired = [
            user_id for user_id, timestamp in _last_export_at.items()
            if now - timestamp >= FORM_EXPORT_COOLDOWN_SECONDS
        ]
        for user_id in expired:
            _last_export_at.pop(user_id, None)
    return 0


async def get_form_responses(form_id: str) -> dict:
    """Fetch form responses without exposing API details to the caller."""
    url = f"https://test.upmini.app/api/forms/{form_id}/responses"
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise FormResponseError("forms API request failed")
                payload = await response.json()
                if not isinstance(payload, dict) or not isinstance(payload.get("responses"), list):
                    raise FormResponseError("forms API returned an invalid payload")
                return payload
    except FormResponseError:
        raise
    except Exception as exc:
        raise FormResponseError("forms API request failed") from exc


def format_value_for_excel(value):
    """Convert values to strings, joining lists with commas."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def generate_excel_file(responses_data: dict, form_id: str) -> str:
    """Generate an Excel file containing form responses."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = f"Responses_{form_id[:8]}"

    all_keys = set()
    for response in responses_data.get("responses", []):
        response_data = response.get("response_data", {})
        if isinstance(response_data, dict):
            all_keys.update(str(key) for key in response_data.keys())
    all_keys = sorted(all_keys)

    headers = ["ID", "Form ID", "Created At"] + all_keys
    for column, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=column, value=_safe_excel_value(header))
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

    for row, response in enumerate(responses_data.get("responses", []), 2):
        worksheet.cell(row=row, column=1, value=_safe_excel_value(response.get("id", "")))
        worksheet.cell(row=row, column=2, value=_safe_excel_value(response.get("form_id", "")))
        worksheet.cell(row=row, column=3, value=_safe_excel_value(response.get("created_at", "")))

        response_data = response.get("response_data", {})
        if not isinstance(response_data, dict):
            response_data = {}
        for column, key in enumerate(all_keys, 4):
            worksheet.cell(row=row, column=column, value=_safe_excel_value(response_data.get(key, "")))

    for column in worksheet.columns:
        max_length = max((len(str(cell.value)) for cell in column if cell.value is not None), default=0)
        worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

    file_descriptor, filepath = tempfile.mkstemp(prefix="form_responses_", suffix=".xlsx")
    os.close(file_descriptor)
    try:
        workbook.save(filepath)
    except Exception:
        try:
            os.remove(filepath)
        except OSError:
            pass
        raise
    return filepath


async def handle_form_res_command(
    message: Message,
    operator_ids: Optional[Union[FrozenSet[int], Set[int]]] = None,
) -> None:
    """Authorize, fetch, and deliver a form response export."""
    actor_id = message.from_user.id if message.from_user else None
    if operator_ids is None:
        operator_ids = parse_operator_ids(os.getenv("FORM_RES_OPERATOR_IDS"))

    if actor_id is None or actor_id not in operator_ids:
        _audit_export("denied", actor_id, reason="not_allowlisted")
        await message.answer("⛔ Команда недоступна.")
        return

    chat_type = getattr(getattr(message, "chat", None), "type", None)
    if chat_type != "private":
        _audit_export("denied", actor_id, reason="private_chat_required")
        await message.answer("⛔ Команда доступна только в личном чате с ботом.")
        return

    command_parts = (message.text or "").strip().split()
    if len(command_parts) != 2:
        _audit_export("invalid_request", actor_id, reason="invalid_arguments")
        await message.answer("❌ Неверный формат команды. Используйте: /form_res <form_id>")
        return

    try:
        form_id = _normalize_form_id(command_parts[1])
    except (ValueError, AttributeError):
        _audit_export("invalid_request", actor_id, reason="invalid_form_id")
        await message.answer("❌ Неверный идентификатор формы.")
        return

    retry_after = _reserve_export(actor_id)
    if retry_after:
        _audit_export(
            "rate_limited",
            actor_id,
            form_id,
            retry_after_seconds=retry_after,
        )
        await message.answer(
            f"⏳ Выгрузка уже запускалась. Повторите через {retry_after} сек."
        )
        return

    _audit_export("started", actor_id, form_id)
    processing_message = None
    excel_filepath = None
    try:
        processing_message = await message.answer("⏳ Получаю ответы формы...")
        responses_data = await get_form_responses(form_id)
        responses = responses_data.get("responses")
        if not isinstance(responses, list):
            raise FormResponseError("forms API returned an invalid payload")
        if not responses:
            _audit_export("not_found", actor_id, form_id, response_count=0)
            await processing_message.edit_text("❌ Ответы для этой формы не найдены.")
            return

        await processing_message.edit_text("📊 Генерирую Excel файл...")
        excel_filepath = generate_excel_file(responses_data, form_id)
        await message.answer_document(
            document=FSInputFile(excel_filepath),
            caption=f"📋 Ответы формы выгружены. Всего ответов: {len(responses)}",
        )
        try:
            await processing_message.delete()
        except Exception:
            logger.warning("form_res_export processing_message_cleanup_failed")
        _audit_export("success", actor_id, form_id, response_count=len(responses))
    except Exception as exc:
        _audit_export("failure", actor_id, form_id, error_type=type(exc).__name__)
        error_text = "❌ Не удалось получить ответы формы. Попробуйте позже."
        if processing_message is not None:
            try:
                await processing_message.edit_text(error_text)
            except Exception:
                pass
        else:
            try:
                await message.answer(error_text)
            except Exception:
                pass
    finally:
        if excel_filepath:
            try:
                os.remove(excel_filepath)
            except OSError:
                logger.warning("form_res_export temp_file_cleanup_failed")
