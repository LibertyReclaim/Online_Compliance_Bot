from typing import Iterable

from config import SUPPORTED_STATES


def validate_required_columns(columns: Iterable[str], required_columns: list[str], file_label: str) -> None:
    missing = sorted(set(required_columns) - set(columns))
    if missing:
        raise ValueError(f"{file_label} is missing required columns: {', '.join(missing)}")


def validate_state_code(state_code: str) -> None:
    if (state_code or "").upper() not in SUPPORTED_STATES:
        raise ValueError(f"Unsupported state code: {state_code}. Supported: {sorted(SUPPORTED_STATES)}")


def validate_holder_exists(holder_id: str, holder_map: dict[str, object]) -> None:
    if holder_id not in holder_map:
        raise ValueError(f"holder_id '{holder_id}' was not found in all_holder_information.xlsx")
