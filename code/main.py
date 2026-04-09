from __future__ import annotations

import argparse
from typing import Iterable

from config import HOLDER_INFORMATION_FILE, PAYMENT_FILE
from models import PaymentRecord, RunResult, StateRunContext
from path_utils import build_naupa_file_path
from state_registry import get_state_runner
from utils import setup_logger
from validation import (
    validate_holder_exists,
    validate_naupa_file_exists,
    validate_required_file_exists,
    validate_state_code,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Online Compliance Bot runner")
    parser.add_argument("--holder-id", help="Filter by holder_id")
    parser.add_argument("--company", help="Filter by company name (case-insensitive contains)")
    parser.add_argument("--state", help="Filter by state abbreviation")
    parser.add_argument("--status", help="Filter by payment status, e.g. pending")
    parser.add_argument("--headless", action="store_true", help="Run Playwright in headless mode")
    return parser.parse_args()


def is_negative_report(amount_to_remit: float) -> bool:
    return float(amount_to_remit) == 0


def filter_payments(payments: Iterable[PaymentRecord], args: argparse.Namespace) -> list[PaymentRecord]:
    filtered = list(payments)
    if args.holder_id:
        filtered = [p for p in filtered if p.holder_id == str(args.holder_id)]
    if args.company:
        company = args.company.strip().lower()
        filtered = [p for p in filtered if company in p.company_name.lower()]
    if args.state:
        filtered = [p for p in filtered if p.state_code == args.state.strip().upper()]
    if args.status:
        filtered = [p for p in filtered if p.status == args.status.strip().lower()]
    return filtered


def ensure_required_input_files() -> None:
    validate_required_file_exists(HOLDER_INFORMATION_FILE, "holder_information.xlsx")
    validate_required_file_exists(PAYMENT_FILE, "payment_file.xlsx")


def run() -> list[RunResult]:
    logger = setup_logger()
    args = parse_args()

    ensure_required_input_files()

    from excel_loader import load_holder_records, load_payment_records

    holders = load_holder_records()
    payments = filter_payments(load_payment_records(), args)
    results: list[RunResult] = []

    if not payments:
        logger.info("No payment rows matched the provided filters.")
        return results

    for payment in payments:
        try:
            validate_holder_exists(payment.holder_id, holders)
            validate_state_code(payment.state_code)

            holder = holders[payment.holder_id]
            negative = is_negative_report(payment.amount_to_remit)
            naupa_path = build_naupa_file_path(payment.company_name, payment.naupa_file_name)
            validate_naupa_file_exists(naupa_path)

            context = StateRunContext(
                state_code=payment.state_code,
                naupa_file_path=naupa_path,
                is_negative_report=negative,
                run_headless=args.headless,
            )

            logger.info(
                "Starting payment_id=%s company=%s state=%s negative=%s file=%s",
                payment.payment_id,
                payment.company_name,
                payment.state_code,
                negative,
                naupa_path,
            )

            runner = get_state_runner(payment.state_code)
            state_output = runner(context=context, company_data=holder.data, payment_data=payment.data)
            results.append(
                RunResult(
                    payment_id=payment.payment_id,
                    state_code=payment.state_code,
                    success=bool(state_output.get("success", True)),
                    message=state_output.get("message", "Completed"),
                    naupa_file_path=naupa_path,
                    details=state_output,
                )
            )
            logger.info("Finished payment_id=%s", payment.payment_id)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed payment_id=%s: %s", payment.payment_id, exc)
            results.append(
                RunResult(
                    payment_id=payment.payment_id,
                    state_code=payment.state_code,
                    success=False,
                    message=str(exc),
                )
            )

    return results


if __name__ == "__main__":
    run()
