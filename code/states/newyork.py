from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any, Iterable

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

TARGET_URL = "https://ouf.osc.ny.gov/app/holder-info"


HOLDER_FIELDS: list[str] = [
    "holder_name",
    "holder_tax_id",
    "holder_id",
    "contact_name",
    "contact_phone",
    "phone_extension",
    "business_is_active",
    "previous_business_name",
    "previous_business_fein",
    "on_behalf_of_another_org",
    "first_time_filing",
    "email",
    "email_confirmation",
    "foreign_address",
    "address_1",
    "address_2",
    "city",
    "state",
    "zip",
    "country",
    "combined_file",
    "parent_company_fein",
]

PAYMENT_FIELDS: list[str] = [
    "report_type",
    "report_year",
    "total_amount",
    "funds_method",
    "naupa_file_name",
]

TEXT_INPUT_FIELDS: list[str] = [
    "holder_name",
    "holder_tax_id",
    "holder_id",
    "contact_name",
    "contact_phone",
    "phone_extension",
    "previous_business_name",
    "previous_business_fein",
    "email",
    "email_confirmation",
    "address_1",
    "address_2",
    "city",
    "zip",
    "parent_company_fein",
    "total_amount",
]

DROPDOWN_FIELDS: list[str] = [
    "state",
    "country",
    "report_type",
    "report_year",
    "funds_method",
]

YES_NO_FIELDS: list[str] = [
    "business_is_active",
    "on_behalf_of_another_org",
    "first_time_filing",
    "foreign_address",
    "combined_file",
]

FIELD_LABELS: dict[str, str] = {
    "holder_name": "Holder Name",
    "holder_tax_id": "Federal Employer Identification Number",
    "holder_id": "Holder ID",
    "contact_name": "Contact Name",
    "contact_phone": "Contact Phone",
    "phone_extension": "Phone Extension",
    "previous_business_name": "Previous Business Name",
    "previous_business_fein": "Previous Business FEIN",
    "email": "Email Address",
    "email_confirmation": "Email Address Confirmation",
    "address_1": "Address 1",
    "address_2": "Address 2",
    "city": "City",
    "state": "State",
    "zip": "Zip",
    "country": "Country",
    "report_type": "Report Type",
    "report_year": "Report Year",
    "funds_method": "Funds Remitted Via",
    "parent_company_fein": "Parent Company FEIN",
    "total_amount": "Total Dollar Amount Remitted",
}

FIELD_NAMES: dict[str, list[str]] = {
    "holder_name": ["holderName", "holder_name"],
    "holder_tax_id": ["holderTaxId", "holder_tax_id", "fein", "federalTaxId"],
    "holder_id": ["holderId", "holder_id"],
    "contact_name": ["contactName", "contact_name"],
    "contact_phone": ["contactPhone", "contact_phone", "phone"],
    "phone_extension": ["phoneExtension", "phone_extension", "ext"],
    "previous_business_name": ["previousBusinessName", "previous_business_name"],
    "previous_business_fein": ["previousBusinessFein", "previous_business_fein"],
    "email": ["email", "emailAddress"],
    "email_confirmation": ["emailConfirmation", "email_confirmation", "confirmEmail"],
    "address_1": ["address1", "address_1"],
    "address_2": ["address2", "address_2"],
    "city": ["city"],
    "state": ["state", "stateCode"],
    "zip": ["zip", "zipCode"],
    "country": ["country", "countryCode"],
    "report_type": ["reportType", "report_type"],
    "report_year": ["reportYear", "report_year", "year"],
    "funds_method": ["fundsMethod", "funds_method", "paymentMethod"],
    "parent_company_fein": ["parentCompanyFein", "parent_company_fein"],
    "total_amount": ["totalAmount", "total_amount", "amount"],
}

FIELD_IDS: dict[str, list[str]] = {
    "state": ["state", "stateCode"],
    "country": ["countryCode", "country"],
    "report_type": ["reportType", "report_type"],
    "report_year": ["reportYear", "report_year"],
    "funds_method": ["fundsMethod", "funds_method"],
    "email_confirmation": ["emailConfirmation", "confirmEmail"],
    "total_amount": ["totalAmount", "amount", "totalDollarAmountRemitted"],
}

QUESTION_TEXTS: dict[str, list[str]] = {
    "business_is_active": ["Business is active:"],
    "on_behalf_of_another_org": [
        "on behalf of another organization",
        "report on behalf",
        "another organization",
    ],
    "first_time_filing": [
        "first time this business entity",
        "first time filing",
        "unclaimed property report",
    ],
    "foreign_address": ["Check for Foreign Address", "Foreign Address", "foreign address"],
    "combined_file": [
        "combined file containing multiple reports",
        "related entities under the same parent company",
        "combined file",
    ],
}


def _log(message: str) -> None:
    print(f"[NY] {message}")


def _normalized_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _safe_locator_count(locator: Locator) -> int:
    try:
        return locator.count()
    except Exception:
        return 0


def _first_visible(locator: Locator) -> Locator | None:
    count = _safe_locator_count(locator)
    for index in range(count):
        candidate = locator.nth(index)
        try:
            if candidate.is_visible():
                return candidate
        except Exception:
            continue
    return None


def _prepare_fill(locator: Locator, field_name: str) -> None:
    _log(f"[{field_name}] scroll_into_view_if_needed")
    locator.scroll_into_view_if_needed(timeout=10_000)
    locator.wait_for(state="visible", timeout=10_000)
    locator.wait_for(state="attached", timeout=10_000)
    locator.wait_for(state="editable", timeout=10_000)


def _try_text_locator(page: Page, strategy: str, field_name: str, pattern: str) -> Locator | None:
    if strategy == "exact_label":
        locator = page.get_by_label(pattern, exact=True)
    elif strategy == "partial_label":
        locator = page.get_by_label(pattern, exact=False)
    elif strategy == "name":
        locator = page.locator(f"input[name='{pattern}'], textarea[name='{pattern}']")
    elif strategy == "id":
        locator = page.locator(f"input[id='{pattern}'], textarea[id='{pattern}']")
    elif strategy == "nearby_label":
        locator = page.get_by_text(pattern, exact=False).locator(
            "xpath=following::input[1] | following::textarea[1]"
        )
    else:
        return None

    count = _safe_locator_count(locator)
    _log(f"[{field_name}] strategy={strategy} pattern={pattern!r} count={count}")
    return _first_visible(locator)


def fill_text_input(
    page: Page,
    field_name: str,
    value: Any,
    labels: list[str] | None = None,
    names: list[str] | None = None,
    ids: list[str] | None = None,
) -> None:
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank value")
        return

    value_text = _to_text(value)
    _log(f"[{field_name}] fill text value={value_text!r}")

    labels = labels or [FIELD_LABELS.get(field_name, field_name.replace("_", " ").title())]
    names = names or FIELD_NAMES.get(field_name, [field_name])
    ids = ids or FIELD_IDS.get(field_name, [field_name])

    strategies: list[tuple[str, str]] = []
    strategies.extend(("exact_label", label) for label in labels)
    strategies.extend(("partial_label", label) for label in labels)
    strategies.extend(("name", name) for name in names)
    strategies.extend(("id", ident) for ident in ids)
    strategies.extend(("nearby_label", label) for label in labels)

    last_error: Exception | None = None
    for strategy, pattern in strategies:
        try:
            candidate = _try_text_locator(page, strategy, field_name, pattern)
            if candidate is None:
                continue

            _prepare_fill(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] filled via strategy={strategy} pattern={pattern!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(
                f"[{field_name}] FAILED strategy={strategy} pattern={pattern!r} "
                f"value={value_text!r}: {exc}\n{traceback.format_exc()}"
            )

    raise RuntimeError(
        f"Unable to fill text field '{field_name}' with value={value_text!r}. "
        f"Last error: {last_error}"
    )


def fill_email_confirmation(page: Page, value: Any) -> None:
    field_name = "email_confirmation"
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank value")
        return

    value_text = _to_text(value)
    _log(f"[{field_name}] using field-specific locator overrides value={value_text!r}")

    strategies: list[tuple[str, Locator]] = [
        ("get_by_label('Email Address Confirmation')", page.get_by_label("Email Address Confirmation", exact=False)),
        ("get_by_label('*Email Address Confirmation')", page.get_by_label("*Email Address Confirmation", exact=False)),
        ("input[name*='confirm' i]", page.locator("input[name*='confirm' i]")),
        ("input[id*='confirm' i]", page.locator("input[id*='confirm' i]")),
        (
            "nearby label 'Email Address Confirmation'",
            page.get_by_text("Email Address Confirmation", exact=False).locator("xpath=following::input[1]"),
        ),
    ]

    last_error: Exception | None = None
    for label, locator in strategies:
        try:
            count = _safe_locator_count(locator)
            _log(f"[{field_name}] strategy={label} count={count}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue

            _prepare_fill(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] filled with strategy={label}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(
                f"[{field_name}] FAILED strategy={label} value={value_text!r}: {exc}\n"
                f"{traceback.format_exc()}"
            )

    raise RuntimeError(
        f"Unable to fill field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def fill_total_amount(page: Page, value: Any) -> None:
    field_name = "total_amount"
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank value")
        return

    value_text = _to_text(value)
    _log(f"[{field_name}] using field-specific locator overrides value={value_text!r}")

    strategies: list[tuple[str, Locator]] = [
        (
            "get_by_label('Total Dollar Amount Remitted')",
            page.get_by_label("Total Dollar Amount Remitted", exact=False),
        ),
        (
            "get_by_label('*Total Dollar Amount Remitted')",
            page.get_by_label("*Total Dollar Amount Remitted", exact=False),
        ),
        (
            "text->following input",
            page.get_by_text("Total Dollar Amount Remitted", exact=False).locator("xpath=following::input[1]"),
        ),
        ("input[name*='amount' i]", page.locator("input[name*='amount' i]").first),
        ("input[id*='amount' i]", page.locator("input[id*='amount' i]").first),
        (
            "nearby label",
            page.get_by_text("Total Dollar Amount Remitted", exact=False).locator("xpath=following::input[1]"),
        ),
    ]

    last_error: Exception | None = None
    for strategy_name, locator in strategies:
        try:
            count = _safe_locator_count(locator)
            _log(f"[{field_name}] strategy={strategy_name} locator_count={count}")
            candidate = _first_visible(locator)
            if candidate is None:
                _log(f"[{field_name}] strategy={strategy_name} no visible candidate")
                continue

            visible = candidate.is_visible()
            _log(f"[{field_name}] strategy={strategy_name} visible={visible}")

            _log(f"[{field_name}] strategy={strategy_name} scrolling")
            candidate.scroll_into_view_if_needed(timeout=10_000)
            _log(f"[{field_name}] strategy={strategy_name} scroll complete")

            candidate.wait_for(state="visible", timeout=10_000)
            candidate.wait_for(state="editable", timeout=10_000)
            candidate.fill(value_text)
            _log(f"[{field_name}] filled with strategy={strategy_name}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(
                f"[{field_name}] FAILED strategy={strategy_name} value={value_text!r}: {exc}\n"
                f"{traceback.format_exc()}"
            )

    raise RuntimeError(
        f"Unable to fill field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def _is_select(locator: Locator) -> bool:
    try:
        return (locator.evaluate("el => el.tagName.toLowerCase()") or "") == "select"
    except Exception:
        return False


def _find_dropdown_candidates(
    page: Page,
    field_name: str,
    labels: Iterable[str],
    names: Iterable[str],
    ids: Iterable[str],
) -> list[tuple[str, Locator]]:
    candidates: list[tuple[str, Locator]] = []

    for label in labels:
        candidates.append((f"get_by_label exact: {label}", page.get_by_label(label, exact=True)))
        candidates.append((f"get_by_label partial: {label}", page.get_by_label(label, exact=False)))

    for name in names:
        candidates.append((f"select[name='{name}']", page.locator(f"select[name='{name}']")))

    for ident in ids:
        candidates.append((f"select[id='{ident}']", page.locator(f"select[id='{ident}']")))

    for label in labels:
        candidates.append(
            (
                f"nearby label -> select: {label}",
                page.get_by_text(label, exact=False).locator("xpath=following::select[1]"),
            )
        )

    return candidates


def select_dropdown(
    page: Page,
    field_name: str,
    value: Any,
    labels: list[str] | None = None,
    names: list[str] | None = None,
    ids: list[str] | None = None,
) -> None:
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank dropdown value")
        return

    value_text = _to_text(value)
    labels = labels or [FIELD_LABELS.get(field_name, field_name.replace("_", " ").title())]
    names = names or FIELD_NAMES.get(field_name, [field_name])
    ids = ids or FIELD_IDS.get(field_name, [field_name])

    _log(
        f"[{field_name}] select dropdown value={value_text!r} labels={labels} names={names} ids={ids}"
    )

    last_error: Exception | None = None
    for strategy_name, locator in _find_dropdown_candidates(page, field_name, labels, names, ids):
        try:
            count = _safe_locator_count(locator)
            _log(f"[{field_name}] strategy={strategy_name} count={count}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue

            if not _is_select(candidate):
                _log(f"[{field_name}] strategy={strategy_name} matched non-select element, skipping")
                continue

            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)

            try:
                candidate.select_option(label=value_text)
                _log(f"[{field_name}] selected by label via {strategy_name}")
                return
            except Exception as by_label_exc:  # noqa: BLE001
                _log(f"[{field_name}] label match failed via {strategy_name}: {by_label_exc}")

            candidate.select_option(value=value_text)
            _log(f"[{field_name}] selected by value via {strategy_name}")
            return

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(
                f"[{field_name}] FAILED dropdown strategy={strategy_name} value={value_text!r}: {exc}\n"
                f"{traceback.format_exc()}"
            )

    raise RuntimeError(
        f"Unable to select dropdown field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def _coerce_yes_no(value: Any) -> str:
    normalized = _normalized_text(value)
    if normalized in {"yes", "y", "true", "1"}:
        return "yes"
    if normalized in {"no", "n", "false", "0"}:
        return "no"
    return normalized


def _find_question_container(page: Page, fragments: list[str]) -> tuple[Locator, str] | None:
    for fragment in fragments:
        locator = page.get_by_text(fragment, exact=False)
        count = _safe_locator_count(locator)
        _log(f"[radio] question fragment={fragment!r} matched_nodes={count}")
        for idx in range(count):
            text_node = locator.nth(idx)
            try:
                if not text_node.is_visible():
                    continue
                container = text_node.locator(
                    "xpath=ancestor::*[self::div or self::fieldset or self::section][1]"
                )
                if _safe_locator_count(container) > 0:
                    return container.first, fragment
            except Exception:
                continue
    return None


def select_yes_no(page: Page, field_name: str, value: Any) -> None:
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank yes/no value")
        return

    desired = _coerce_yes_no(value)
    if desired not in {"yes", "no"}:
        raise ValueError(f"Unsupported yes/no value for {field_name}: {value!r}")

    fragments = QUESTION_TEXTS.get(field_name, [])
    if not fragments:
        raise KeyError(f"No question text mapping configured for field: {field_name}")

    _log(f"[{field_name}] select yes/no desired={desired!r} fragments={fragments}")
    result = _find_question_container(page, fragments)
    if result is None:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    container, matched_fragment = result
    radio_candidates = container.locator("input[type='radio']")
    candidate_count = _safe_locator_count(radio_candidates)
    _log(
        f"[{field_name}] matched question fragment={matched_fragment!r}; "
        f"radio_candidates_in_container={candidate_count}"
    )

    if candidate_count == 0:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    chosen_radio: Locator | None = None
    chosen_id = ""
    for idx in range(candidate_count):
        radio = radio_candidates.nth(idx)
        radio_id = radio.get_attribute("id") or ""
        radio_value = _normalized_text(radio.get_attribute("value"))
        aria_label = _normalized_text(radio.get_attribute("aria-label"))

        radio_label_text = ""
        if radio_id:
            label_for_radio = page.locator(f"label[for='{radio_id}']")
            if _safe_locator_count(label_for_radio) > 0:
                radio_label_text = _normalized_text(label_for_radio.first.inner_text())

        if desired in {radio_value, aria_label, radio_label_text}:
            chosen_radio = radio
            chosen_id = radio_id
            break

    if chosen_radio is None:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    _log(f"[{field_name}] chosen_radio_id={chosen_id!r}")

    label_click_succeeded = False
    fallback_set_checked = False

    if chosen_id:
        matching_label = page.locator(f"label[for='{chosen_id}']")
        label_count = _safe_locator_count(matching_label)
        _log(f"[{field_name}] matching_label_count={label_count}")
        if label_count > 0:
            try:
                matching_label.first.scroll_into_view_if_needed(timeout=10_000)
                matching_label.first.click(timeout=10_000)
                label_click_succeeded = True
                _log(f"[{field_name}] clicked label for radio id={chosen_id!r}")
            except Exception as exc:  # noqa: BLE001
                _log(f"[{field_name}] label click failed id={chosen_id!r}: {exc}")

    if not label_click_succeeded:
        chosen_radio.set_checked(True)
        fallback_set_checked = True
        _log(f"[{field_name}] fallback set_checked(True) used")

    final_checked = chosen_radio.is_checked()
    _log(
        f"[{field_name}] final_checked={final_checked} label_click_succeeded={label_click_succeeded} "
        f"fallback_set_checked={fallback_set_checked}"
    )

    if not final_checked:
        raise RuntimeError(f"Could not set yes/no radio for field: {field_name}")


def _click_next(page: Page, step_name: str) -> None:
    _log(f"[{step_name}] clicking Next")
    next_candidates = [
        page.get_by_role("button", name="Next", exact=True),
        page.get_by_role("button", name="Next", exact=False),
        page.locator("button:has-text('Next')"),
        page.locator("input[type='button'][value='Next'], input[type='submit'][value='Next']"),
    ]

    last_error: Exception | None = None
    for idx, locator in enumerate(next_candidates, start=1):
        try:
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.click(timeout=10_000)
            _log(f"[{step_name}] Next clicked with strategy #{idx}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{step_name}] Next click strategy #{idx} failed: {exc}")

    raise RuntimeError(f"Unable to click Next button for step '{step_name}'. Last error: {last_error}")


def _upload_naupa_file(page: Page, naupa_file_path: Path) -> None:
    _log(f"[upload] uploading NAUPA file path={naupa_file_path}")
    if not naupa_file_path.exists():
        raise FileNotFoundError(f"NAUPA file does not exist: {naupa_file_path}")

    upload_candidates = [
        page.locator("input[type='file']"),
        page.locator("input[type='file'][accept*='txt' i]"),
        page.get_by_label("Upload", exact=False),
        page.get_by_text("Upload", exact=False).locator("xpath=following::input[@type='file'][1]"),
    ]

    last_error: Exception | None = None
    for idx, locator in enumerate(upload_candidates, start=1):
        try:
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            candidate.set_input_files(str(naupa_file_path))
            _log(f"[upload] file uploaded using strategy #{idx}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[upload] strategy #{idx} failed: {exc}\n{traceback.format_exc()}")

    raise RuntimeError(f"Unable to upload NAUPA file: {naupa_file_path}. Last error: {last_error}")


def _wait_for_preview(page: Page) -> None:
    _log("[preview] waiting for preview/signature indicators")
    preview_indicators = [
        page.get_by_text("Electronic Signature", exact=False),
        page.get_by_text("Preview", exact=False),
        page.get_by_text("Review", exact=False),
        page.get_by_text("I certify", exact=False),
    ]

    timeout_at = time.time() + 60
    while time.time() < timeout_at:
        for locator in preview_indicators:
            candidate = _first_visible(locator)
            if candidate is not None:
                _log("[preview] detected preview indicator")
                return
        page.wait_for_timeout(500)

    raise PlaywrightTimeoutError("Timed out waiting for preview/signature page indicators.")


def _merged_context(holder_data: dict[str, Any], payment_data: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for field in HOLDER_FIELDS:
        if field in holder_data:
            context[field] = holder_data.get(field)
    for field in PAYMENT_FIELDS:
        if field in payment_data:
            context[field] = payment_data.get(field)
    return context


def _run_with_page(page: Page, holder_data: dict[str, Any], payment_data: dict[str, Any], naupa_file_path: str | Path) -> None:
    """Internal NY flow implementation using explicit page and NAUPA path."""
    merged = _merged_context(holder_data, payment_data)
    naupa_path = Path(naupa_file_path)

    _log(f"Opening target URL: {TARGET_URL}")
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60_000)

    # text fields
    for field in TEXT_INPUT_FIELDS:
        try:
            if field == "email_confirmation":
                fill_email_confirmation(page, merged.get(field))
            elif field == "total_amount":
                fill_total_amount(page, merged.get(field))
            else:
                fill_text_input(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _log(
                f"[ERROR] field={field} value={merged.get(field)!r} type=text error={exc}\n"
                f"{traceback.format_exc()}"
            )
            raise

    # dropdown fields
    dropdown_overrides = {
        "country": {
            "labels": ["Country"],
            "names": ["countryCode", "country"],
            "ids": ["countryCode", "country"],
        },
        "state": {
            "labels": ["State"],
            "names": ["state", "stateCode"],
            "ids": ["state", "stateCode"],
        },
        "report_year": {
            "labels": ["Report Year"],
            "names": ["reportYear", "year"],
            "ids": ["reportYear", "report_year"],
        },
        "report_type": {
            "labels": ["Report Type"],
            "names": ["reportType"],
            "ids": ["reportType"],
        },
        "funds_method": {
            "labels": ["Funds Remitted Via", "Funds Method"],
            "names": ["fundsMethod", "paymentMethod"],
            "ids": ["fundsMethod", "paymentMethod"],
        },
    }

    for field in DROPDOWN_FIELDS:
        try:
            overrides = dropdown_overrides.get(field, {})
            select_dropdown(
                page,
                field,
                merged.get(field),
                labels=overrides.get("labels"),
                names=overrides.get("names"),
                ids=overrides.get("ids"),
            )
        except Exception as exc:  # noqa: BLE001
            _log(
                f"[ERROR] field={field} value={merged.get(field)!r} type=dropdown error={exc}\n"
                f"{traceback.format_exc()}"
            )
            raise

    # yes/no fields
    for field in YES_NO_FIELDS:
        try:
            select_yes_no(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _log(
                f"[ERROR] field={field} value={merged.get(field)!r} type=yes_no error={exc}\n"
                f"{traceback.format_exc()}"
            )
            raise

    _click_next(page, "holder_info")
    page.wait_for_timeout(1_000)

    _upload_naupa_file(page, naupa_path)
    _click_next(page, "upload")

    _wait_for_preview(page)
    print("Reached preview page. Review, sign, and submit manually.")

    # Keep browser session alive for manual sign/submit.
    _log("Pausing indefinitely for manual review/sign/submit.")
    while True:
        page.wait_for_timeout(60_000)


def run(context: Any, company_data: dict[str, Any], payment_data: dict[str, Any]) -> dict[str, Any]:
    """
    Public NY runner compatible with main.py registry invocation:
    run(context, company_data, payment_data)

    Expected context attributes:
    - page: Playwright Page object
    - naupa_file_path: path to the NAUPA txt file
    """
    page = getattr(context, "page", None)
    naupa_file_path = getattr(context, "naupa_file_path", None)

    if page is None:
        raise ValueError(
            "New York runner requires context.page (Playwright Page). "
            "Attach a Page object to context before invoking run()."
        )
    if naupa_file_path is None:
        raise ValueError("New York runner requires context.naupa_file_path.")

    _run_with_page(
        page=page,
        holder_data=company_data,
        payment_data=payment_data,
        naupa_file_path=naupa_file_path,
    )

    return {
        "success": True,
        "message": "Reached preview page. Review, sign, and submit manually.",
        "state": "NY",
        "naupa_file": str(naupa_file_path),
    }
