import re
from typing import FrozenSet, Optional


_TELEGRAM_ID_RE = re.compile(r"^[0-9]+$")


def parse_operator_ids(raw_value: Optional[str]) -> FrozenSet[int]:
    """Parse a comma-separated Telegram user ID allowlist, denying on bad input."""
    if raw_value is None or not raw_value.strip():
        return frozenset()

    parts = [part.strip() for part in raw_value.split(",")]
    if any(len(part) > 20 or not _TELEGRAM_ID_RE.fullmatch(part) for part in parts):
        return frozenset()

    operator_ids = {int(part) for part in parts}
    if any(operator_id <= 0 for operator_id in operator_ids):
        return frozenset()

    return frozenset(operator_ids)
