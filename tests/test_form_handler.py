import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import form_handler
from access_control import parse_operator_ids
from form_handler import handle_form_res_command


FORM_ID = "0f913c81-cc46-42cd-9a0b-8458a8da2a2a"


class FakeProcessingMessage:
    def __init__(self):
        self.edited_text = []
        self.deleted = False

    async def edit_text(self, text):
        self.edited_text.append(text)

    async def delete(self):
        self.deleted = True


class FakeMessage:
    def __init__(self, user_id, text):
        self.from_user = SimpleNamespace(id=user_id) if user_id is not None else None
        self.chat = SimpleNamespace(type="private")
        self.text = text
        self.answers = []
        self.processing_message = FakeProcessingMessage()
        self.documents = []

    async def answer(self, text):
        self.answers.append(text)
        return self.processing_message

    async def answer_document(self, document, caption):
        self.documents.append((document, caption))
        self.assert_file_exists_during_upload = os.path.exists(document.path)


class FormExportAccessTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        form_handler._last_export_at.clear()

    async def test_missing_allowlist_denies_without_calling_api(self):
        message = FakeMessage(2468, f"/form_res {FORM_ID}")
        with patch.dict(os.environ, {}, clear=True), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock
        ) as get_responses:
            with self.assertLogs("form_handler", level="INFO") as logs:
                await handle_form_res_command(message)

        get_responses.assert_not_awaited()
        self.assertEqual(message.answers, ["⛔ Команда недоступна."])
        self.assertIn("event=denied", "\n".join(logs.output))
        self.assertNotIn(str(2468), "\n".join(logs.output))

    async def test_invalid_allowlist_fails_closed(self):
        self.assertEqual(parse_operator_ids("123,not-an-id"), frozenset())
        self.assertEqual(parse_operator_ids("-123"), frozenset())

        message = FakeMessage(2468, f"/form_res {FORM_ID}")
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "123,invalid"}, clear=True), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock
        ) as get_responses:
            await handle_form_res_command(message)

        get_responses.assert_not_awaited()
        self.assertEqual(message.answers, ["⛔ Команда недоступна."])

    async def test_user_outside_configured_allowlist_is_denied(self):
        message = FakeMessage(2468, f"/form_res {FORM_ID}")
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "1234"}, clear=True), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock
        ) as get_responses:
            await handle_form_res_command(message)

        get_responses.assert_not_awaited()
        self.assertEqual(message.answers, ["⛔ Команда недоступна."])

    async def test_export_is_denied_in_group_chat(self):
        message = FakeMessage(2468, f"/form_res {FORM_ID}")
        message.chat.type = "group"
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "2468"}, clear=True), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock
        ) as get_responses:
            await handle_form_res_command(message)

        get_responses.assert_not_awaited()
        self.assertEqual(message.answers, ["⛔ Команда доступна только в личном чате с ботом."])

    async def test_authorized_operator_gets_export_and_audit_omits_response_content(self):
        response_secret = "private-response@example.test"
        message = FakeMessage(2468, f"/form_res {FORM_ID}")
        payload = {
            "responses": [
                {
                    "id": "response-id-secret",
                    "form_id": FORM_ID,
                    "created_at": "2026-09-21T10:00:00Z",
                    "response_data": {"email": response_secret, "phone": "+79990000000"},
                }
            ],
            "total": 1,
        }
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "2468"}, clear=True), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock, return_value=payload
        ):
            with self.assertLogs("form_handler", level="INFO") as logs:
                await handle_form_res_command(message)

        self.assertEqual(len(message.documents), 1)
        document, caption = message.documents[0]
        self.assertTrue(message.assert_file_exists_during_upload)
        self.assertFalse(os.path.exists(document.path))
        self.assertIn("Всего ответов: 1", caption)
        self.assertTrue(message.processing_message.deleted)
        audit = "\n".join(logs.output)
        self.assertIn("event=success", audit)
        for sensitive_value in (response_secret, "+79990000000", "response-id-secret", FORM_ID):
            self.assertNotIn(sensitive_value, audit)

    async def test_invalid_uuid_is_rejected_before_api_call(self):
        invalid_form_id = "not-a-uuid-secret"
        message = FakeMessage(2468, f"/form_res {invalid_form_id}")
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "2468"}, clear=True), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock
        ) as get_responses:
            with self.assertLogs("form_handler", level="INFO") as logs:
                await handle_form_res_command(message)

        get_responses.assert_not_awaited()
        self.assertEqual(message.answers, ["❌ Неверный идентификатор формы."])
        self.assertNotIn(invalid_form_id, "\n".join(logs.output))

    async def test_api_exception_details_are_not_sent_or_logged(self):
        message = FakeMessage(2468, f"/form_res {FORM_ID}")
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "2468"}, clear=True), patch(
            "form_handler.get_form_responses",
            new_callable=AsyncMock,
            side_effect=RuntimeError("token=secret response=person@example.test"),
        ):
            with self.assertLogs("form_handler", level="INFO") as logs:
                await handle_form_res_command(message)

        user_messages = "\n".join(message.answers + message.processing_message.edited_text)
        audit = "\n".join(logs.output)
        self.assertIn("Не удалось получить ответы формы", user_messages)
        self.assertNotIn("token=secret", user_messages)
        self.assertNotIn("token=secret", audit)
        self.assertNotIn("person@example.test", audit)

    async def test_export_cooldown_limits_repeat_requests_before_api_call(self):
        first = FakeMessage(2468, f"/form_res {FORM_ID}")
        second = FakeMessage(2468, f"/form_res {FORM_ID}")
        payload = {"responses": [{"id": "response-1", "response_data": {"name": "Synthetic"}}]}
        with patch.dict(os.environ, {"FORM_RES_OPERATOR_IDS": "2468"}, clear=True), patch(
            "form_handler.monotonic", side_effect=[100.0, 101.0]
        ), patch(
            "form_handler.get_form_responses", new_callable=AsyncMock, return_value=payload
        ) as get_responses:
            with self.assertLogs("form_handler", level="INFO") as logs:
                await handle_form_res_command(first)
                await handle_form_res_command(second)

        get_responses.assert_awaited_once_with(FORM_ID)
        self.assertEqual(second.answers, ["⏳ Выгрузка уже запускалась. Повторите через 59 сек."])
        self.assertIn("event=rate_limited", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
