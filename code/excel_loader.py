from __future__ import annotations

from typing import Any

import pandas as pd

from config import HOLDER_INFORMATION_FILE, PAYMENT_FILE
from models import HolderRecord, PaymentRecord
from validation import validate_required_columns

REQUIRED_HOLDER_COLUMNS = [
    "holder_id",
    "company_name",
    "holder_name",
    "contact_name",
    "contact_phone",
    "email",
]

REQUIRED_PAYMENT_COLUMNS = [
    "payment_id",
    "holder_id",
    "company_name",
    "state_code",
    "amount_to_remit",
    "funds_remitted_via",
    "report_year",
    "report_type",
    "naupa_file_name",
    "status",
    "notes",
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
    df = pd.read_excel(HOLDER_INFORMATION_FILE, engine="openpyxl")
    df = _normalize_dataframe(df)
    validate_required_columns(df.columns, REQUIRED_HOLDER_COLUMNS, "holder_information.xlsx")

    holders: dict[str, HolderRecord] = {}
    for row in df.to_dict(orient="records"):
        cleaned = {k: _clean_value(v) for k, v in row.items()}
        holder_id = str(cleaned["holder_id"]).strip()
        holders[holder_id] = HolderRecord(holder_id=holder_id, data=cleaned)
    return holders


def load_payment_records() -> list[PaymentRecord]:
    df = pd.read_excel(PAYMENT_FILE, engine="openpyxl")
    df = _normalize_dataframe(df)
    validate_required_columns(df.columns, REQUIRED_PAYMENT_COLUMNS, "payment_file.xlsx")

    payments: list[PaymentRecord] = []
    for row in df.to_dict(orient="records"):
        cleaned = {k: _clean_value(v) for k, v in row.items()}
        amount = float(cleaned.get("amount_to_remit") or 0)
        payments.append(
            PaymentRecord(
                payment_id=str(cleaned["payment_id"]).strip(),
                holder_id=str(cleaned["holder_id"]).strip(),
                company_name=str(cleaned.get("company_name") or "").strip(),
                state_code=str(cleaned.get("state_code") or "").strip().upper(),
                amount_to_remit=amount,
                naupa_file_name=str(cleaned.get("naupa_file_name") or "").strip(),
                status=str(cleaned.get("status") or "").strip().lower(),
                data=cleaned,
            )
        )
    return payments
