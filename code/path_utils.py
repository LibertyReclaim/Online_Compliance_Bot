from pathlib import Path

from config import PROJECT_ROOT


def sanitize_company_folder_name(company_name: str) -> str:
    return (company_name or "").strip()


def build_company_folder_path(company_name: str) -> Path:
    return PROJECT_ROOT / sanitize_company_folder_name(company_name)


def construct_naupa_file_name(company_name: str, state_code: str, report_year: str | int) -> str:
    safe_company_name = sanitize_company_folder_name(company_name)
    safe_state = str(state_code or "").strip().upper()
    safe_year = str(report_year or "").strip()
    return f"{safe_company_name}_{safe_state} {safe_year} NAUPA.txt"


def build_naupa_file_path(company_name: str, state_code: str, report_year: str | int) -> Path:
    file_name = construct_naupa_file_name(company_name, state_code, report_year)
    return build_company_folder_path(company_name) / file_name
