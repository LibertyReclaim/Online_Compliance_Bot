from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StateContext:
    state_code: str
    naupa_file_path: Path
    is_negative_report: bool
    run_headless: bool = False


def build_result(success: bool, message: str, **details: Any) -> dict[str, Any]:
    return {
        "success": success,
        "message": message,
        "details": details,
    }
