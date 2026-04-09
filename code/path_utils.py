from pathlib import Path

from config import PROJECT_ROOT


def sanitize_company_folder_name(company_name: str) -> str:
    return (company_name or "").strip()


def build_company_folder_path(company_name: str) -> Path:
    return PROJECT_ROOT / sanitize_company_folder_name(company_name)


def build_naupa_file_path(company_name: str, file_name: str) -> Path:
    return build_company_folder_path(company_name) / file_name
