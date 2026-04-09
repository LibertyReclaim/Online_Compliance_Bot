from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
CLIENTS_DIR = PROJECT_ROOT / "clients"
STATES_DIR = PROJECT_ROOT / "states"
LOGS_DIR = PROJECT_ROOT / "logs"

HOLDER_WORKBOOK = SAMPLE_DATA_DIR / "all_holder_information.xlsx"
FILING_WORKBOOK = SAMPLE_DATA_DIR / "filing_queue.xlsx"

SUPPORTED_STATES = {"AL", "AK", "AR", "CA", "CO", "CT", "DE", "ID", "IL", "IN"}
