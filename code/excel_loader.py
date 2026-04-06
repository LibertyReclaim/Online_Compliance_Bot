from __future__ import annotations

from typing import Any

import pandas as pd

from config import FILING_WORKBOOK, HOLDER_WORKBOOK
from models import FilingRecord, HolderRecord
from validation import validate_required_columns

REQUIRED_HOLDER_COLUMNS = [
    "holder_id",
    "company_name",
    "holder_name",
    "contact_name",
    "contact_phone",
    "email",
]

REQUIRED_FILING_COLUMNS = [
    "filing_id",
    "holder_id",
    "company_name",
    "state_code",
    "amount_to_remit",
    "naupa_file_name",
    "status",
]


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    df = df.where(pd.notna(df), None)
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].map(lambda value: value.strip() if isinstance(value, str) else value)
    return df


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def load_holder_records() -> dict[str, HolderRecord]:
    df = pd.read_excel(HOLDER_WORKBOOK, engine="openpyxl")
    df = _normalize_dataframe(df)
    validate_required_columns(df.columns, REQUIRED_HOLDER_COLUMNS, "all_holder_information.xlsx")

    holders: dict[str, HolderRecord] = {}
    for row in df.to_dict(orient="records"):
        cleaned = {k: _clean_value(v) for k, v in row.items()}
        holder_id = str(cleaned["holder_id"]).strip()
        holders[holder_id] = HolderRecord(holder_id=holder_id, data=cleaned)
    return holders


def load_filing_records() -> list[FilingRecord]:
    df = pd.read_excel(FILING_WORKBOOK, engine="openpyxl")
    df = _normalize_dataframe(df)
    validate_required_columns(df.columns, REQUIRED_FILING_COLUMNS, "filing_execution.xlsx")

    filings: list[FilingRecord] = []
    for row in df.to_dict(orient="records"):
        cleaned = {k: _clean_value(v) for k, v in row.items()}
        amount = float(cleaned.get("amount_to_remit") or 0)
        filings.append(
            FilingRecord(
                filing_id=str(cleaned["filing_id"]).strip(),
                holder_id=str(cleaned["holder_id"]).strip(),
                company_name=str(cleaned.get("company_name") or "").strip(),
                state_code=str(cleaned.get("state_code") or "").strip().upper(),
                amount_to_remit=amount,
                naupa_file_name=str(cleaned.get("naupa_file_name") or "").strip(),
                status=str(cleaned.get("status") or "").strip().lower(),
                data=cleaned,
            )
        )
    return filings
