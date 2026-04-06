from __future__ import annotations

import argparse
from typing import Iterable

from config import FILING_WORKBOOK, HOLDER_WORKBOOK
from models import FilingRecord, RunResult
from path_utils import build_naupa_file_path
from state_registry import get_state_runner
from states.base_state import StateContext
from utils import setup_logger
from validation import validate_holder_exists, validate_state_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Online Compliance Bot runner")
    parser.add_argument("--holder-id", help="Filter by holder_id")
    parser.add_argument("--company", help="Filter by company name (case-insensitive contains)")
    parser.add_argument("--state", help="Filter by state abbreviation")
    parser.add_argument("--status", help="Filter by filing status, e.g. pending")
    parser.add_argument("--headless", action="store_true", help="Run Playwright in headless mode")
    return parser.parse_args()


def is_negative_report(amount_to_remit: float) -> bool:
    return float(amount_to_remit) <= 0


def filter_filings(filings: Iterable[FilingRecord], args: argparse.Namespace) -> list[FilingRecord]:
    filtered = list(filings)
    if args.holder_id:
        filtered = [f for f in filtered if f.holder_id == str(args.holder_id)]
    if args.company:
        company = args.company.strip().lower()
        filtered = [f for f in filtered if company in f.company_name.lower()]
    if args.state:
        filtered = [f for f in filtered if f.state_code == args.state.strip().upper()]
    if args.status:
        filtered = [f for f in filtered if f.status == args.status.strip().lower()]
    return filtered




def ensure_required_input_files() -> None:
    required_files = [
        (HOLDER_WORKBOOK, "all_holder_information.xlsx"),
        (FILING_WORKBOOK, "filing_execution.xlsx"),
    ]
    for file_path, display_name in required_files:
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required file: {display_name}. Please create it manually.")

def run() -> list[RunResult]:
    logger = setup_logger()
    args = parse_args()

    ensure_required_input_files()

    from excel_loader import load_filing_records, load_holder_records

    holders = load_holder_records()
    filings = filter_filings(load_filing_records(), args)
    results: list[RunResult] = []

    if not filings:
        logger.info("No filings matched the provided filters.")
        return results

    for filing in filings:
        try:
            validate_holder_exists(filing.holder_id, holders)
            validate_state_code(filing.state_code)

            holder = holders[filing.holder_id]
            negative = is_negative_report(filing.amount_to_remit)
            naupa_path = build_naupa_file_path(filing.company_name, filing.naupa_file_name)

            context = StateContext(
                state_code=filing.state_code,
                naupa_file_path=naupa_path,
                is_negative_report=negative,
                run_headless=args.headless,
            )

            logger.info(
                "Starting filing_id=%s company=%s state=%s negative=%s file=%s",
                filing.filing_id,
                filing.company_name,
                filing.state_code,
                negative,
                naupa_path,
            )

            runner = get_state_runner(filing.state_code)
            state_output = runner(context=context, company_data=holder.data, filing_data=filing.data)
            results.append(
                RunResult(
                    filing_id=filing.filing_id,
                    state_code=filing.state_code,
                    success=bool(state_output.get("success", True)),
                    message=state_output.get("message", "Completed"),
                    naupa_file_path=naupa_path,
                    details=state_output,
                )
            )
            logger.info("Finished filing_id=%s", filing.filing_id)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed filing_id=%s: %s", filing.filing_id, exc)
            results.append(
                RunResult(
                    filing_id=filing.filing_id,
                    state_code=filing.state_code,
                    success=False,
                    message=str(exc),
                )
            )

    return results


if __name__ == "__main__":
    run()
