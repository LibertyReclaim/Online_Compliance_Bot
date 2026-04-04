import re
from pathlib import Path

from config import CLIENTS_DIR, PROJECT_ROOT


def resolve_project_root() -> Path:
    return PROJECT_ROOT


def sanitize_company_folder_name(company_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]", "", company_name or "")
    return cleaned.strip()


def build_company_folder_path(company_name: str) -> Path:
    return CLIENTS_DIR / sanitize_company_folder_name(company_name)


def build_naupa_file_path(company_name: str, state_code: str, file_name: str) -> Path:
    return build_company_folder_path(company_name) / state_code.upper() / file_name
