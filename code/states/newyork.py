from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

TARGET_URL = "https://ouf.osc.ny.gov/app/holder-info"

# Source workbook + visible NY label mapping.
FIELD_CONFIG: dict[str, dict[str, str]] = {
    "holder_name": {"source": "holder", "label": "*Holder Name:"},
    "holder_tax_id": {"source": "holder", "label": "*Holder Tax ID:"},
    "holder_id": {"source": "holder", "label": "Holder ID:"},
    "contact_name": {"source": "holder", "label": "*Contact Name:"},
    "contact_phone": {"source": "holder", "label": "*Contact Phone Number:"},
    "phone_extension": {"source": "holder", "label": "Phone Extension:"},
    "business_is_active": {"source": "holder", "label": "*Business is active:"},
    "previous_business_name": {"source": "holder", "label": "Previous Business Name (if applicable):"},
    "previous_business_fein": {"source": "holder", "label": "Previous Business FEIN (if applicable):"},
    "on_behalf_of_another_org": {
        "source": "holder",
        "label": "Is this report on behalf of another organization?:",
    },
    "first_time_filing": {
        "source": "holder",
        "label": "Is this the first time this business entity has filed an Unclaimed Property Report?:",
    },
    "email": {"source": "holder", "label": "*Email Address:"},
    "email_confirmation": {"source": "holder", "label": "*Email Address Confirmation:"},
    "foreign_address": {"source": "holder", "label": "Check for Foreign Address:"},
    "address_1": {"source": "holder", "label": "*Address 1:"},
    "address_2": {"source": "holder", "label": "Address 2:"},
    "city": {"source": "holder", "label": "*City:"},
    "state": {"source": "holder", "label": "*State:"},
    "zip": {"source": "holder", "label": "*ZIP Code:"},
    "country": {"source": "holder", "label": "*Country:"},
    "combined_file": {
        "source": "holder",
        "label": "*Is this a combined file containing multiple reports for related entities under the same parent company?:",
    },
    "parent_company_fein": {"source": "holder", "label": "Parent Company FEIN:"},
    "report_type": {"source": "payment", "label": "*Report Type:"},
    "report_year": {"source": "payment", "label": "*Report Year:"},
    "amount_to_remit": {"source": "payment", "label": "*Total Dollar Amount Remitted:"},
    "funds_remitted_via": {"source": "payment", "label": "*Funds Remitted Via:"},
}

TEXT_INPUT_FIELDS = [
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
    "amount_to_remit",
]

DROPDOWN_FIELDS = ["state", "country", "report_type", "report_year", "funds_remitted_via"]
YES_NO_FIELDS = ["business_is_active", "on_behalf_of_another_org", "first_time_filing", "combined_file"]
CHECKBOX_FIELDS = ["foreign_address"]

HOLDER_FIELDS = [
    "holder_id",
    "company_name",
    "holder_name",
    "holder_tax_id",
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

PAYMENT_FIELDS = [
    "payment_id",
    "holder_id",
    "company_name",
    "state_code",
    "amount_to_remit",
    "funds_remitted_via",
    "report_year",
    "report_type",
    "naupa_file_name",
    "status",
    "notes",
]


def _log(message: str) -> None:
    print(f"[NY] {message}")


def _field_log(field_name: str, message: str) -> None:
    source = FIELD_CONFIG.get(field_name, {}).get("source", "unknown")
    label = FIELD_CONFIG.get(field_name, {}).get("label", field_name)
    _log(f"field={field_name} source={source} label={label!r} {message}")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _count(locator: Locator) -> int:
    try:
        return locator.count()
    except Exception:
        return 0


def _first_visible(locator: Locator) -> Locator | None:
    for i in range(_count(locator)):
        candidate = locator.nth(i)
        try:
            if candidate.is_visible():
                return candidate
        except Exception:
            continue
    return None


def _prepare_input(locator: Locator, field_name: str) -> None:
    _field_log(field_name, "strategy=prepare_input scroll + wait")
    locator.scroll_into_view_if_needed(timeout=10_000)
    locator.wait_for(state="visible", timeout=10_000)
    locator.wait_for(state="editable", timeout=10_000)


def _find_text_anchor(page: Page, label: str) -> Locator | None:
    # Prefer exact text first, then partial.
    exact = page.get_by_text(label, exact=True)
    if _count(exact) > 0:
        candidate = _first_visible(exact)
        if candidate is not None:
            return candidate

    partial = page.get_by_text(label, exact=False)
    return _first_visible(partial)


def _following_input_from_label(page: Page, field_name: str, label: str) -> Locator | None:
    anchor = _find_text_anchor(page, label)
    if anchor is None:
        _field_log(field_name, f"strategy=nearby_input label_anchor_not_found label={label!r}")
        return None

    locator = anchor.locator("xpath=following::input[1]")
    _field_log(field_name, f"strategy=nearby_input label={label!r} locator_count={_count(locator)}")
    return _first_visible(locator)


def _following_select_from_label(page: Page, field_name: str, label: str) -> Locator | None:
    anchor = _find_text_anchor(page, label)
    if anchor is None:
        _field_log(field_name, f"strategy=nearby_select label_anchor_not_found label={label!r}")
        return None

    locator = anchor.locator("xpath=following::select[1]")
    _field_log(field_name, f"strategy=nearby_select label={label!r} locator_count={_count(locator)}")
    return _first_visible(locator)


def fill_text_input(page: Page, field_name: str, value: Any) -> None:
    if _is_blank(value):
        _field_log(field_name, "skipped=blank")
        return

    value_text = _to_text(value)
    label = FIELD_CONFIG[field_name]["label"]
    _field_log(field_name, f"value={value_text!r}")

    last_error: Exception | None = None

    # 1) get_by_label using exact visible label text.
    try:
        by_label = page.get_by_label(label, exact=False)
        _field_log(field_name, f"strategy=get_by_label locator_count={_count(by_label)}")
        candidate = _first_visible(by_label)
        if candidate is not None:
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _field_log(field_name, "strategy=get_by_label matched=success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=get_by_label failed error={exc}")

    # 2) nearby label -> first following input.
    try:
        candidate = _following_input_from_label(page, field_name, label)
        if candidate is not None:
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _field_log(field_name, "strategy=nearby_label_following_input matched=success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=nearby_label_following_input failed error={exc}")

    # 3) input[name*=... i]
    try:
        hint = field_name.replace("_", "")
        by_name = page.locator(f"input[name*='{hint}' i]")
        _field_log(field_name, f"strategy=name_contains locator_count={_count(by_name)}")
        candidate = _first_visible(by_name)
        if candidate is not None:
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _field_log(field_name, "strategy=name_contains matched=success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=name_contains failed error={exc}")

    # 4) input[id*=... i]
    try:
        hint = field_name.replace("_", "")
        by_id = page.locator(f"input[id*='{hint}' i]")
        _field_log(field_name, f"strategy=id_contains locator_count={_count(by_id)}")
        candidate = _first_visible(by_id)
        if candidate is not None:
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _field_log(field_name, "strategy=id_contains matched=success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=id_contains failed error={exc}")

    raise RuntimeError(
        f"Unable to fill text field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def fill_email_confirmation(page: Page, value: Any) -> None:
    # Keep explicit override with same NY label logic.
    field_name = "email_confirmation"
    if _is_blank(value):
        _field_log(field_name, "skipped=blank")
        return

    value_text = _to_text(value)
    label = FIELD_CONFIG[field_name]["label"]
    _field_log(field_name, f"override value={value_text!r}")

    strategies = [
        ("get_by_label", page.get_by_label(label, exact=False)),
        ("input[name*='confirm' i]", page.locator("input[name*='confirm' i]")),
        ("input[id*='confirm' i]", page.locator("input[id*='confirm' i]")),
    ]

    last_error: Exception | None = None
    for strategy_name, locator in strategies:
        try:
            _field_log(field_name, f"strategy={strategy_name} locator_count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _field_log(field_name, f"strategy={strategy_name} matched=success")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _field_log(field_name, f"strategy={strategy_name} failed error={exc}")

    try:
        candidate = _following_input_from_label(page, field_name, label)
        if candidate is not None:
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _field_log(field_name, "strategy=nearby_label_following_input matched=success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=nearby_label_following_input failed error={exc}")

    raise RuntimeError(
        f"Unable to fill field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def fill_total_amount(page: Page, value: Any) -> None:
    # Keep explicit override with exact visible label.
    field_name = "amount_to_remit"
    if _is_blank(value):
        _field_log(field_name, "skipped=blank")
        return

    value_text = _to_text(value)
    label = FIELD_CONFIG[field_name]["label"]
    _field_log(field_name, f"override value={value_text!r}")

    # 1) get_by_label
    by_label = page.get_by_label(label, exact=False)
    _field_log(field_name, f"strategy=get_by_label locator_count={_count(by_label)}")
    candidate = _first_visible(by_label)
    if candidate is not None:
        _prepare_input(candidate, field_name)
        candidate.fill(value_text)
        _field_log(field_name, "strategy=get_by_label matched=success")
        return

    # 2) nearby label -> following input
    candidate = _following_input_from_label(page, field_name, label)
    if candidate is not None:
        _prepare_input(candidate, field_name)
        candidate.fill(value_text)
        _field_log(field_name, "strategy=nearby_label_following_input matched=success")
        return

    # 3) amount hints
    for strategy_name, locator in [
        ("input[name*='amount' i]", page.locator("input[name*='amount' i]")),
        ("input[id*='amount' i]", page.locator("input[id*='amount' i]")),
    ]:
        _field_log(field_name, f"strategy={strategy_name} locator_count={_count(locator)}")
        candidate = _first_visible(locator)
        if candidate is None:
            continue
        _prepare_input(candidate, field_name)
        candidate.fill(value_text)
        _field_log(field_name, f"strategy={strategy_name} matched=success")
        return

    raise RuntimeError(f"Unable to fill field '{field_name}' with value={value_text!r}")


def _is_select(locator: Locator) -> bool:
    try:
        return (locator.evaluate("el => el.tagName.toLowerCase()") or "") == "select"
    except Exception:
        return False


def select_dropdown(page: Page, field_name: str, value: Any) -> None:
    if _is_blank(value):
        _field_log(field_name, "skipped=blank")
        return

    value_text = _to_text(value)
    label = FIELD_CONFIG[field_name]["label"]
    _field_log(field_name, f"dropdown value={value_text!r}")

    last_error: Exception | None = None

    # 1) label-based select lookup.
    try:
        by_label = page.get_by_label(label, exact=False)
        _field_log(field_name, f"strategy=get_by_label locator_count={_count(by_label)}")
        candidate = _first_visible(by_label)
        if candidate is not None and _is_select(candidate):
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)
            try:
                candidate.select_option(label=value_text)
                _field_log(field_name, "strategy=get_by_label select_option(label=...) success")
            except Exception:
                candidate.select_option(value=value_text)
                _field_log(field_name, "strategy=get_by_label select_option(value=...) success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=get_by_label failed error={exc}")

    # 2) nearby label -> following select.
    try:
        candidate = _following_select_from_label(page, field_name, label)
        if candidate is not None and _is_select(candidate):
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)
            try:
                candidate.select_option(label=value_text)
                _field_log(field_name, "strategy=nearby_label_following_select select_option(label=...) success")
            except Exception:
                candidate.select_option(value=value_text)
                _field_log(field_name, "strategy=nearby_label_following_select select_option(value=...) success")
            return
    except Exception as exc:  # noqa: BLE001
        last_error = exc
        _field_log(field_name, f"strategy=nearby_label_following_select failed error={exc}")

    raise RuntimeError(
        f"Unable to select dropdown field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def _coerce_yes_no(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"yes", "y", "true", "1"}:
        return "yes"
    if normalized in {"no", "n", "false", "0"}:
        return "no"
    return normalized


def select_yes_no(page: Page, field_name: str, value: Any) -> None:
    if _is_blank(value):
        _field_log(field_name, "skipped=blank")
        return

    desired = _coerce_yes_no(value)
    if desired not in {"yes", "no"}:
        raise ValueError(f"Unsupported yes/no value for field {field_name}: {value!r}")

    label = FIELD_CONFIG[field_name]["label"]
    _field_log(field_name, f"radio desired={desired!r}")

    anchor = _find_text_anchor(page, label)
    if anchor is None:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    container = anchor.locator("xpath=ancestor::*[self::div or self::fieldset or self::section][1]")
    scope = container.first if _count(container) > 0 else anchor

    radios = scope.locator("input[type='radio']")
    _field_log(field_name, f"radio candidates count={_count(radios)}")
    if _count(radios) == 0:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    chosen: Locator | None = None
    chosen_id = ""
    for i in range(_count(radios)):
        radio = radios.nth(i)
        radio_id = radio.get_attribute("id") or ""
        radio_value = str(radio.get_attribute("value") or "").strip().lower()
        label_text = ""
        if radio_id:
            matching_label = page.locator(f"label[for='{radio_id}']")
            if _count(matching_label) > 0:
                label_text = str(matching_label.first.inner_text() or "").strip().lower()
        if desired in {radio_value, label_text}:
            chosen = radio
            chosen_id = radio_id
            break

    if chosen is None:
        raise RuntimeError(f"Could not locate radio option '{desired}' for field: {field_name}")

    label_click_succeeded = False
    if chosen_id:
        matching_label = page.locator(f"label[for='{chosen_id}']")
        _field_log(field_name, f"matching label count={_count(matching_label)} chosen_id={chosen_id!r}")
        if _count(matching_label) > 0:
            try:
                matching_label.first.scroll_into_view_if_needed(timeout=10_000)
                matching_label.first.click(timeout=10_000)
                label_click_succeeded = True
                _field_log(field_name, "label click success")
            except Exception as exc:  # noqa: BLE001
                _field_log(field_name, f"label click failed error={exc}")

    if not label_click_succeeded:
        chosen.set_checked(True)
        _field_log(field_name, "fallback set_checked(True) used")

    if not chosen.is_checked():
        raise RuntimeError(f"Could not set yes/no radio for field: {field_name}")


def set_foreign_address_checkbox(page: Page, value: Any) -> None:
    field_name = "foreign_address"
    desired = _coerce_yes_no(value)
    _field_log(field_name, f"checkbox desired={desired!r}")

    if desired != "yes":
        _field_log(field_name, "leaving unchecked (value is no/blank)")
        return

    label = FIELD_CONFIG[field_name]["label"]
    anchor = _find_text_anchor(page, label)
    if anchor is None:
        raise RuntimeError(f"Could not locate checkbox for field: {field_name}")

    checkbox = anchor.locator("xpath=following::input[@type='checkbox'][1]")
    _field_log(field_name, f"checkbox candidates count={_count(checkbox)}")
    candidate = _first_visible(checkbox)
    if candidate is None:
        raise RuntimeError(f"Could not locate checkbox for field: {field_name}")

    if candidate.is_checked():
        _field_log(field_name, "already checked")
        return

    checkbox_id = candidate.get_attribute("id") or ""
    if checkbox_id:
        label_for_checkbox = page.locator(f"label[for='{checkbox_id}']")
        _field_log(field_name, f"checkbox label count={_count(label_for_checkbox)}")
        if _count(label_for_checkbox) > 0:
            try:
                label_for_checkbox.first.scroll_into_view_if_needed(timeout=10_000)
                label_for_checkbox.first.click(timeout=10_000)
                _field_log(field_name, "checkbox checked via label click")
                return
            except Exception as exc:  # noqa: BLE001
                _field_log(field_name, f"checkbox label click failed error={exc}")

    candidate.set_checked(True)
    _field_log(field_name, "checkbox checked via set_checked(True)")


def _click_next(page: Page, step: str) -> None:
    _log(f"[{step}] click Next")
    candidates = [
        page.get_by_role("button", name="Next", exact=True),
        page.get_by_role("button", name="Next", exact=False),
        page.locator("button:has-text('Next')"),
        page.locator("input[type='button'][value='Next'], input[type='submit'][value='Next']"),
    ]

    last_error: Exception | None = None
    for idx, locator in enumerate(candidates, start=1):
        try:
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.click(timeout=10_000)
            _log(f"[{step}] Next clicked strategy #{idx}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{step}] Next strategy #{idx} failed error={exc}")

    raise RuntimeError(f"Unable to click Next on step '{step}'. Last error: {last_error}")


def _upload_naupa_file(page: Page, naupa_file_path: Path) -> None:
    _log(f"[upload] path={naupa_file_path}")
    if not naupa_file_path.exists():
        raise FileNotFoundError(f"NAUPA file does not exist: {naupa_file_path}")

    candidates = [
        page.locator("input[type='file']"),
        page.locator("input[type='file'][accept*='txt' i]"),
        page.get_by_label("Upload", exact=False),
    ]

    last_error: Exception | None = None
    for idx, locator in enumerate(candidates, start=1):
        try:
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            candidate.set_input_files(str(naupa_file_path))
            _log(f"[upload] success strategy #{idx}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[upload] strategy #{idx} failed error={exc}\n{traceback.format_exc()}")

    raise RuntimeError(f"Unable to upload NAUPA file: {naupa_file_path}. Last error: {last_error}")


def _wait_for_preview(page: Page) -> None:
    indicators = [
        page.get_by_text("Electronic Signature", exact=False),
        page.get_by_text("Preview", exact=False),
        page.get_by_text("Review", exact=False),
        page.get_by_text("I certify", exact=False),
    ]

    timeout_at = time.time() + 60
    while time.time() < timeout_at:
        for locator in indicators:
            if _first_visible(locator) is not None:
                _log("[preview] reached preview/signature page")
                return
        page.wait_for_timeout(500)

    raise PlaywrightTimeoutError("Timed out waiting for preview/signature indicators.")


def _merged_context(holder_data: dict[str, Any], payment_data: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for field in HOLDER_FIELDS:
        if field in holder_data:
            merged[field] = holder_data.get(field)
    for field in PAYMENT_FIELDS:
        if field in payment_data:
            merged[field] = payment_data.get(field)
    return merged


def _run_with_page(page: Page, holder_data: dict[str, Any], payment_data: dict[str, Any], naupa_file_path: str | Path) -> None:
    merged = _merged_context(holder_data, payment_data)
    naupa_path = Path(naupa_file_path)

    _log(f"Opening URL: {TARGET_URL}")
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60_000)

    for field in TEXT_INPUT_FIELDS:
        try:
            if field == "email_confirmation":
                fill_email_confirmation(page, merged.get(field))
            elif field == "amount_to_remit":
                fill_total_amount(page, merged.get(field))
            else:
                fill_text_input(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _field_log(field, f"error={exc} value={merged.get(field)!r}\n{traceback.format_exc()}")
            raise

    for field in DROPDOWN_FIELDS:
        try:
            select_dropdown(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _field_log(field, f"error={exc} value={merged.get(field)!r}\n{traceback.format_exc()}")
            raise

    for field in YES_NO_FIELDS:
        try:
            select_yes_no(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _field_log(field, f"error={exc} value={merged.get(field)!r}\n{traceback.format_exc()}")
            raise

    for field in CHECKBOX_FIELDS:
        try:
            set_foreign_address_checkbox(page, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _field_log(field, f"error={exc} value={merged.get(field)!r}\n{traceback.format_exc()}")
            raise

    _click_next(page, "holder_info")
    page.wait_for_timeout(1_000)

    _upload_naupa_file(page, naupa_path)
    _click_next(page, "upload")

    _wait_for_preview(page)
    print("Reached preview page. Review, sign, and submit manually.")

    _log("Pausing indefinitely for manual review/sign/submit.")
    while True:
        page.wait_for_timeout(60_000)


def run(context: Any, company_data: dict[str, Any], payment_data: dict[str, Any]) -> dict[str, Any]:
    page = getattr(context, "page", None)
    naupa_file_path = getattr(context, "naupa_file_path", None)

    if page is None:
        raise ValueError(
            "New York runner requires context.page (Playwright Page). "
            "Attach a Page object to context before invoking run()."
        )
    if naupa_file_path is None:
        raise ValueError("New York runner requires context.naupa_file_path.")

    _run_with_page(page=page, holder_data=company_data, payment_data=payment_data, naupa_file_path=naupa_file_path)

    return {
        "success": True,
        "message": "Reached preview page. Review, sign, and submit manually.",
        "state": "NY",
        "naupa_file": str(naupa_file_path),
    }
