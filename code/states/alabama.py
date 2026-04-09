from __future__ import annotations

from typing import Any

from states.base_state import StateContext, build_result

TARGET_URL = "https://example.com/alabama-unclaimed-property"


def run_alabama(context: StateContext, company_data: dict[str, Any], filing_data: dict[str, Any]) -> dict[str, Any]:
    # TODO: open browser and navigate to TARGET_URL
    # TODO: fill holder info from company_data
    # TODO: fill filing/report info from filing_data
    # TODO: upload context.naupa_file_path when required
    # TODO: submit and capture confirmation
    return build_result(
        success=True,
        message="AL stub executed. Replace with real automation.",
        target_url=TARGET_URL,
        state=context.state_code,
        negative_report=context.is_negative_report,
        naupa_file=str(context.naupa_file_path),
    )
