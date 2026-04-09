from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
HOLDER_INFORMATION_FILE = PROJECT_ROOT / "holder_information.xlsx"
PAYMENT_FILE = PROJECT_ROOT / "payment_file.xlsx"
STATES_DIR = PROJECT_ROOT / "code" / "states"
SUPPORTED_STATES = {"AL", "AK", "AR", "CA", "CO", "CT", "DE", "ID", "IL", "IN"}
