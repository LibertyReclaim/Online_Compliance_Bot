from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
HOLDER_WORKBOOK = PROJECT_ROOT / "all_holder_information.xlsx"
FILING_WORKBOOK = PROJECT_ROOT / "filing_execution.xlsx"
STATES_DIR = PROJECT_ROOT / "code" / "states"
SUPPORTED_STATES = {"AL", "AK", "AR", "CA", "CO", "CT", "DE", "ID", "IL", "IN"}
