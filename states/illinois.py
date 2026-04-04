from __future__ import annotations

from typing import Any

from states.base_state import StateContext, build_result

TARGET_URL = "https://example.com/illinois-unclaimed-property"


def run_illinois(context: StateContext, company_data: dict[str, Any], filing_data: dict[str, Any]) -> dict[str, Any]:
    """Stubbed IL state automation runner."""
    # TODO: open Playwright browser and navigate to TARGET_URL
    # TODO: fill holder/company information from company_data
    # TODO: fill filing/report fields from filing_data
    # TODO: if not context.is_negative_report, upload context.naupa_file_path
    # TODO: submit filing and capture confirmation details

    return build_result(
        success=True,
        message="IL stub executed. Replace with real Playwright steps.",
        target_url=TARGET_URL,
        state=context.state_code,
        negative_report=context.is_negative_report,
        naupa_file=str(context.naupa_file_path),
    )
