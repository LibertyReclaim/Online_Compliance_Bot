from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HolderRecord:
    holder_id: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class FilingRecord:
    filing_id: str
    holder_id: str
    company_name: str
    state_code: str
    amount_to_remit: float
    naupa_file_name: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    filing_id: str
    state_code: str
    success: bool
    message: str
    naupa_file_path: Path | None = None
    details: dict[str, Any] = field(default_factory=dict)
