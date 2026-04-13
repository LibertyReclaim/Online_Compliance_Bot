from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any

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

DROPDOWN_FIELDS: list[str] = ["state", "country", "report_type", "report_year", "funds_method"]

YES_NO_FIELDS: list[str] = [
    "business_is_active",
    "on_behalf_of_another_org",
    "first_time_filing",
    "foreign_address",
    "combined_file",
]

# Explicit NY visible label candidates (asterisk + colon variants included).
FIELD_LABEL_CANDIDATES: dict[str, list[str]] = {
    "holder_name": ["Holder Name", "*Holder Name", "Holder Name:", "*Holder Name:"],
    "holder_tax_id": ["Holder Tax ID", "*Holder Tax ID", "Holder Tax ID:", "*Holder Tax ID:"],
    "holder_id": ["Holder ID", "Holder ID:"],
    "contact_name": ["Contact Name", "*Contact Name", "Contact Name:", "*Contact Name:"],
    "contact_phone": [
        "Contact Phone Number",
        "*Contact Phone Number",
        "Contact Phone Number:",
        "*Contact Phone Number:",
    ],
    "phone_extension": ["Phone Extension", "Phone Extension:"],
    "email": ["Email Address", "*Email Address", "Email Address:", "*Email Address:"],
    "email_confirmation": [
        "Email Address Confirmation",
        "*Email Address Confirmation",
        "Email Address Confirmation:",
        "*Email Address Confirmation:",
    ],
    "address_1": ["Address 1", "*Address 1", "Address 1:", "*Address 1:"],
    "address_2": ["Address 2", "Address 2:"],
    "city": ["City", "*City", "City:", "*City:"],
    "state": ["State", "*State", "State:", "*State:"],
    "zip": ["ZIP Code", "*ZIP Code", "ZIP Code:", "*ZIP Code:"],
    "country": ["Country", "*Country", "Country:", "*Country:"],
    "report_type": ["Report Type", "*Report Type", "Report Type:", "*Report Type:"],
    "report_year": ["Report Year", "*Report Year", "Report Year:", "*Report Year:"],
    "total_amount": [
        "Total Dollar Amount Remitted",
        "*Total Dollar Amount Remitted",
        "Total Dollar Amount Remitted:",
        "*Total Dollar Amount Remitted:",
    ],
    "funds_method": ["Funds Remitted Via", "*Funds Remitted Via", "Funds Remitted Via:", "*Funds Remitted Via:"],
}

FIELD_HINTS: dict[str, list[str]] = {
    "holder_name": ["holder", "name"],
    "holder_tax_id": ["tax", "fein", "holderTaxId"],
    "holder_id": ["holderId", "holder_id"],
    "contact_name": ["contact", "name"],
    "contact_phone": ["contact", "phone"],
    "phone_extension": ["extension", "ext"],
    "previous_business_name": ["previous", "business", "name"],
    "previous_business_fein": ["previous", "fein"],
    "email": ["email"],
    "email_confirmation": ["confirm", "email"],
    "address_1": ["address1", "address_1"],
    "address_2": ["address2", "address_2"],
    "city": ["city"],
    "state": ["state", "stateCode"],
    "zip": ["zip", "zipcode", "zipCode"],
    "country": ["country", "countryCode"],
    "report_type": ["report", "type"],
    "report_year": ["report", "year", "year"],
    "funds_method": ["funds", "method", "payment"],
    "parent_company_fein": ["parent", "fein"],
    "total_amount": ["amount", "total"],
}

QUESTION_TEXTS: dict[str, list[str]] = {
    "business_is_active": ["Business is active:"],
    "on_behalf_of_another_org": ["on behalf of another organization", "report on behalf", "another organization"],
    "first_time_filing": ["first time this business entity", "first time filing", "unclaimed property report"],
    "foreign_address": ["Check for Foreign Address", "Foreign Address", "foreign address"],
    "combined_file": [
        "combined file containing multiple reports",
        "related entities under the same parent company",
        "combined file",
    ],
}


def _log(message: str) -> None:
    print(f"[NY] {message}")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _count(locator: Locator) -> int:
    try:
        return locator.count()
    except Exception:
        return 0


def _first_visible(locator: Locator) -> Locator | None:
    for idx in range(_count(locator)):
        candidate = locator.nth(idx)
        try:
            if candidate.is_visible():
                return candidate
        except Exception:
            continue
    return None


def _prepare_input(locator: Locator, field_name: str) -> None:
    _log(f"[{field_name}] scroll into view")
    locator.scroll_into_view_if_needed(timeout=10_000)
    locator.wait_for(state="visible", timeout=10_000)
    locator.wait_for(state="editable", timeout=10_000)


def _label_candidates(field_name: str) -> list[str]:
    candidates = FIELD_LABEL_CANDIDATES.get(field_name)
    if candidates:
        return candidates
    # Fallback for fields not explicitly listed.
    title = field_name.replace("_", " ").title()
    return [title, f"*{title}", f"{title}:", f"*{title}:"]


def _find_following_input_from_label(page: Page, field_name: str, label_candidate: str) -> Locator | None:
    _log(f"[{field_name}] nearby-label attempt label={label_candidate!r}")
    label_nodes = page.get_by_text(label_candidate, exact=False)
    _log(f"[{field_name}] nearby-label label_nodes count={_count(label_nodes)}")

    for idx in range(_count(label_nodes)):
        node = label_nodes.nth(idx)
        try:
            if not node.is_visible():
                continue
            input_locator = node.locator("xpath=following::input[1]")
            _log(f"[{field_name}] nearby-label following input count={_count(input_locator)}")
            candidate = _first_visible(input_locator)
            if candidate is not None:
                return candidate
        except Exception:
            continue
    return None


def _find_following_select_from_label(page: Page, field_name: str, label_candidate: str) -> Locator | None:
    _log(f"[{field_name}] nearby-select attempt label={label_candidate!r}")
    label_nodes = page.get_by_text(label_candidate, exact=False)
    _log(f"[{field_name}] nearby-select label_nodes count={_count(label_nodes)}")

    for idx in range(_count(label_nodes)):
        node = label_nodes.nth(idx)
        try:
            if not node.is_visible():
                continue
            select_locator = node.locator("xpath=following::select[1]")
            _log(f"[{field_name}] nearby-select following select count={_count(select_locator)}")
            candidate = _first_visible(select_locator)
            if candidate is not None:
                return candidate
        except Exception:
            continue
    return None


def fill_text_input(page: Page, field_name: str, value: Any) -> None:
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank value")
        return

    value_text = _to_text(value)
    labels = _label_candidates(field_name)
    hints = FIELD_HINTS.get(field_name, [field_name])

    _log(f"[{field_name}] fill value={value_text!r}")
    _log(f"[{field_name}] label candidates={labels}")

    last_error: Exception | None = None

    # 1) get_by_label() using all label candidates.
    for label in labels:
        try:
            locator = page.get_by_label(label, exact=False)
            _log(f"[{field_name}] strategy=get_by_label label={label!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=get_by_label label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=get_by_label label={label!r}: {exc}")

    # 2) Nearby label text -> first following input.
    for label in labels:
        try:
            candidate = _find_following_input_from_label(page, field_name, label)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=nearby_label_following_input label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=nearby_label_following_input label={label!r}: {exc}")

    # 3) input[name*=... i]
    for hint in hints:
        try:
            locator = page.locator(f"input[name*='{hint}' i]")
            _log(f"[{field_name}] strategy=name_contains hint={hint!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=name_contains hint={hint!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=name_contains hint={hint!r}: {exc}")

    # 4) input[id*=... i]
    for hint in hints:
        try:
            locator = page.locator(f"input[id*='{hint}' i]")
            _log(f"[{field_name}] strategy=id_contains hint={hint!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=id_contains hint={hint!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=id_contains hint={hint!r}: {exc}")

    raise RuntimeError(
        f"Unable to fill text field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def fill_email_confirmation(page: Page, value: Any) -> None:
    field_name = "email_confirmation"
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank value")
        return

    value_text = _to_text(value)
    labels = _label_candidates(field_name)
    _log(f"[{field_name}] override fill value={value_text!r} labels={labels}")

    strategies: list[tuple[str, Locator]] = []
    for label in labels:
        strategies.append((f"get_by_label({label!r})", page.get_by_label(label, exact=False)))
    strategies.extend(
        [
            ("input[name*='confirm' i]", page.locator("input[name*='confirm' i]")),
            ("input[id*='confirm' i]", page.locator("input[id*='confirm' i]")),
        ]
    )

    last_error: Exception | None = None
    for strategy_name, locator in strategies:
        try:
            _log(f"[{field_name}] strategy={strategy_name} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy={strategy_name}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy={strategy_name}: {exc}")

    for label in labels:
        try:
            candidate = _find_following_input_from_label(page, field_name, label)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=nearby_label_following_input label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=nearby_label_following_input label={label!r}: {exc}")

    raise RuntimeError(
        f"Unable to fill field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def fill_total_amount(page: Page, value: Any) -> None:
    field_name = "total_amount"
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank value")
        return

    value_text = _to_text(value)
    labels = _label_candidates(field_name)
    _log(f"[{field_name}] override fill value={value_text!r} labels={labels}")

    last_error: Exception | None = None

    # Explicit required order with label variants.
    for label in labels:
        try:
            locator = page.get_by_label(label, exact=False)
            _log(f"[{field_name}] strategy=get_by_label label={label!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=get_by_label label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=get_by_label label={label!r}: {exc}")

    for label in labels:
        try:
            locator = page.get_by_text(label, exact=False).locator("xpath=following::input[1]")
            _log(f"[{field_name}] strategy=text_following_input label={label!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=text_following_input label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=text_following_input label={label!r}: {exc}")

    for strategy_name, locator in [
        ("input[name*='amount' i]", page.locator("input[name*='amount' i]")),
        ("input[id*='amount' i]", page.locator("input[id*='amount' i]")),
    ]:
        try:
            _log(f"[{field_name}] strategy={strategy_name} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy={strategy_name}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy={strategy_name}: {exc}")

    for label in labels:
        try:
            candidate = _find_following_input_from_label(page, field_name, label)
            if candidate is None:
                continue
            _prepare_input(candidate, field_name)
            candidate.fill(value_text)
            _log(f"[{field_name}] SUCCESS strategy=nearby_label_following_input label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=nearby_label_following_input label={label!r}: {exc}")

    raise RuntimeError(
        f"Unable to fill field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def _is_select(locator: Locator) -> bool:
    try:
        return (locator.evaluate("el => el.tagName.toLowerCase()") or "") == "select"
    except Exception:
        return False


def select_dropdown(page: Page, field_name: str, value: Any) -> None:
    if _is_blank(value):
        _log(f"[{field_name}] skipped blank dropdown value")
        return

    value_text = _to_text(value)
    labels = _label_candidates(field_name)
    hints = FIELD_HINTS.get(field_name, [field_name])

    _log(f"[{field_name}] dropdown value={value_text!r}")
    _log(f"[{field_name}] label candidates={labels}")

    last_error: Exception | None = None

    # get_by_label with all candidates
    for label in labels:
        try:
            locator = page.get_by_label(label, exact=False)
            _log(f"[{field_name}] strategy=get_by_label label={label!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None or not _is_select(candidate):
                continue
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)
            try:
                candidate.select_option(label=value_text)
                _log(f"[{field_name}] SUCCESS select_option(label=...) label={label!r}")
            except Exception:
                candidate.select_option(value=value_text)
                _log(f"[{field_name}] SUCCESS select_option(value=...) label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=get_by_label label={label!r}: {exc}")

    # nearby label text -> following select
    for label in labels:
        try:
            candidate = _find_following_select_from_label(page, field_name, label)
            if candidate is None or not _is_select(candidate):
                continue
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)
            try:
                candidate.select_option(label=value_text)
                _log(f"[{field_name}] SUCCESS select_option(label=...) nearby label={label!r}")
            except Exception:
                candidate.select_option(value=value_text)
                _log(f"[{field_name}] SUCCESS select_option(value=...) nearby label={label!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=nearby_label_following_select label={label!r}: {exc}")

    # select[name*=... i]
    for hint in hints:
        try:
            locator = page.locator(f"select[name*='{hint}' i]")
            _log(f"[{field_name}] strategy=name_contains hint={hint!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None or not _is_select(candidate):
                continue
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)
            try:
                candidate.select_option(label=value_text)
                _log(f"[{field_name}] SUCCESS select_option(label=...) name hint={hint!r}")
            except Exception:
                candidate.select_option(value=value_text)
                _log(f"[{field_name}] SUCCESS select_option(value=...) name hint={hint!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=name_contains hint={hint!r}: {exc}")

    # select[id*=... i]
    for hint in hints:
        try:
            locator = page.locator(f"select[id*='{hint}' i]")
            _log(f"[{field_name}] strategy=id_contains hint={hint!r} count={_count(locator)}")
            candidate = _first_visible(locator)
            if candidate is None or not _is_select(candidate):
                continue
            candidate.scroll_into_view_if_needed(timeout=10_000)
            candidate.wait_for(state="visible", timeout=10_000)
            try:
                candidate.select_option(label=value_text)
                _log(f"[{field_name}] SUCCESS select_option(label=...) id hint={hint!r}")
            except Exception:
                candidate.select_option(value=value_text)
                _log(f"[{field_name}] SUCCESS select_option(value=...) id hint={hint!r}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{field_name}] FAIL strategy=id_contains hint={hint!r}: {exc}")

    raise RuntimeError(
        f"Unable to select dropdown field '{field_name}' with value={value_text!r}. Last error: {last_error}"
    )


def _coerce_yes_no(value: Any) -> str:
    normalized = _normalized(value)
    if normalized in {"yes", "y", "true", "1"}:
        return "yes"
    if normalized in {"no", "n", "false", "0"}:
        return "no"
    return normalized


def _find_question_container(page: Page, fragments: list[str]) -> tuple[Locator, str] | None:
    for fragment in fragments:
        nodes = page.get_by_text(fragment, exact=False)
        _log(f"[radio] fragment={fragment!r} nodes={_count(nodes)}")
        for idx in range(_count(nodes)):
            node = nodes.nth(idx)
            try:
                if not node.is_visible():
                    continue
                container = node.locator("xpath=ancestor::*[self::div or self::fieldset or self::section][1]")
                if _count(container) > 0:
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

    result = _find_question_container(page, fragments)
    if result is None:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    container, matched_fragment = result
    radios = container.locator("input[type='radio']")
    radio_count = _count(radios)
    _log(f"[{field_name}] desired={desired} fragment={matched_fragment!r} radios={radio_count}")
    if radio_count == 0:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    chosen: Locator | None = None
    chosen_id = ""
    for idx in range(radio_count):
        radio = radios.nth(idx)
        radio_id = radio.get_attribute("id") or ""
        radio_value = _normalized(radio.get_attribute("value"))
        aria_label = _normalized(radio.get_attribute("aria-label"))
        label_text = ""
        if radio_id:
            labels = page.locator(f"label[for='{radio_id}']")
            if _count(labels) > 0:
                label_text = _normalized(labels.first.inner_text())
        if desired in {radio_value, aria_label, label_text}:
            chosen = radio
            chosen_id = radio_id
            break

    if chosen is None:
        raise RuntimeError(f"Could not locate radio group for field: {field_name}")

    _log(f"[{field_name}] chosen_radio_id={chosen_id!r}")
    label_click_succeeded = False

    if chosen_id:
        labels = page.locator(f"label[for='{chosen_id}']")
        _log(f"[{field_name}] matching label count={_count(labels)}")
        if _count(labels) > 0:
            try:
                labels.first.scroll_into_view_if_needed(timeout=10_000)
                labels.first.click(timeout=10_000)
                label_click_succeeded = True
                _log(f"[{field_name}] clicked label for id={chosen_id!r}")
            except Exception as exc:  # noqa: BLE001
                _log(f"[{field_name}] label click failed: {exc}")

    if not label_click_succeeded:
        chosen.set_checked(True)
        _log(f"[{field_name}] fallback set_checked(True)")

    final_state = chosen.is_checked()
    _log(f"[{field_name}] final checked={final_state}")
    if not final_state:
        raise RuntimeError(f"Could not set yes/no radio for field: {field_name}")


def _click_next(page: Page, step_name: str) -> None:
    _log(f"[{step_name}] click Next")
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
            _log(f"[{step_name}] Next success strategy #{idx}")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            _log(f"[{step_name}] Next failed strategy #{idx}: {exc}")

    raise RuntimeError(f"Unable to click Next for step '{step_name}'. Last error: {last_error}")


def _upload_naupa_file(page: Page, naupa_file_path: Path) -> None:
    _log(f"[upload] file path={naupa_file_path}")
    if not naupa_file_path.exists():
        raise FileNotFoundError(f"NAUPA file does not exist: {naupa_file_path}")

    candidates = [
        page.locator("input[type='file']"),
        page.locator("input[type='file'][accept*='txt' i]"),
        page.get_by_label("Upload", exact=False),
        page.get_by_text("Upload", exact=False).locator("xpath=following::input[@type='file'][1]"),
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
            _log(f"[upload] failed strategy #{idx}: {exc}\n{traceback.format_exc()}")

    raise RuntimeError(f"Unable to upload NAUPA file: {naupa_file_path}. Last error: {last_error}")


def _wait_for_preview(page: Page) -> None:
    _log("[preview] waiting for indicators")
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

    raise PlaywrightTimeoutError("Timed out waiting for preview/signature page indicators.")


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

    _log(f"Open URL: {TARGET_URL}")
    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60_000)

    for field in TEXT_INPUT_FIELDS:
        try:
            if field == "email_confirmation":
                fill_email_confirmation(page, merged.get(field))
            elif field == "total_amount":
                fill_total_amount(page, merged.get(field))
            else:
                fill_text_input(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _log(f"[ERROR] text field={field} value={merged.get(field)!r} error={exc}\n{traceback.format_exc()}")
            raise

    for field in DROPDOWN_FIELDS:
        try:
            select_dropdown(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _log(
                f"[ERROR] dropdown field={field} value={merged.get(field)!r} error={exc}\n{traceback.format_exc()}"
            )
            raise

    for field in YES_NO_FIELDS:
        try:
            select_yes_no(page, field, merged.get(field))
        except Exception as exc:  # noqa: BLE001
            _log(f"[ERROR] yes/no field={field} value={merged.get(field)!r} error={exc}\n{traceback.format_exc()}")
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
