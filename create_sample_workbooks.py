from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import SAMPLE_DATA_DIR


def build_holder_workbook(path: Path) -> None:
    holder_columns = [
        "holder_id", "company_name", "holder_name", "holder_tax_id", "holder_id_secondary",
        "state_tax_id", "contact_name", "contact_title", "contact_phone", "phone_extension",
        "email", "email_confirmation", "address_1", "address_2", "address_3", "city",
        "state", "zip_code", "country", "state_of_incorporation", "date_of_incorporation",
        "reporting_agent_name", "reporting_agent_fein", "number_of_employees",
        "annual_sales_premiums", "total_assets", "notes",
        "custom_field_1", "custom_field_2", "custom_field_3", "custom_field_4", "custom_field_5",
    ]

    rows = [
        {
            "holder_id": "1", "company_name": "Amazon", "holder_name": "Amazon.com, Inc.",
            "holder_tax_id": "91-1646860", "holder_id_secondary": "AMZ-001", "state_tax_id": "AMZ-ST-01",
            "contact_name": "Alexa Booker", "contact_title": "Compliance Manager", "contact_phone": "206-555-0100",
            "phone_extension": "101", "email": "compliance@amazon.com", "email_confirmation": "compliance@amazon.com",
            "address_1": "410 Terry Ave N", "address_2": "", "address_3": "", "city": "Seattle",
            "state": "WA", "zip_code": "98109", "country": "USA", "state_of_incorporation": "DE",
            "date_of_incorporation": "1994-07-05", "reporting_agent_name": "Amazon Reporting Services",
            "reporting_agent_fein": "91-1646860", "number_of_employees": 1500000,
            "annual_sales_premiums": 100000000, "total_assets": 500000000, "notes": "Sample Amazon holder.",
            "custom_field_1": "", "custom_field_2": "", "custom_field_3": "", "custom_field_4": "", "custom_field_5": "",
        },
        {
            "holder_id": "2", "company_name": "Walmart", "holder_name": "Walmart Inc.",
            "holder_tax_id": "71-0415188", "holder_id_secondary": "WMT-002", "state_tax_id": "WMT-ST-02",
            "contact_name": "Sam Ledger", "contact_title": "Tax Lead", "contact_phone": "479-555-0200",
            "phone_extension": "202", "email": "upreporting@walmart.com", "email_confirmation": "upreporting@walmart.com",
            "address_1": "702 SW 8th St", "address_2": "", "address_3": "", "city": "Bentonville",
            "state": "AR", "zip_code": "72716", "country": "USA", "state_of_incorporation": "DE",
            "date_of_incorporation": "1969-10-31", "reporting_agent_name": "Walmart Compliance Group",
            "reporting_agent_fein": "71-0415188", "number_of_employees": 2100000,
            "annual_sales_premiums": 120000000, "total_assets": 420000000, "notes": "Sample Walmart holder.",
            "custom_field_1": "", "custom_field_2": "", "custom_field_3": "", "custom_field_4": "", "custom_field_5": "",
        },
        {
            "holder_id": "3", "company_name": "Target", "holder_name": "Target Corporation",
            "holder_tax_id": "41-0215170", "holder_id_secondary": "TGT-003", "state_tax_id": "TGT-ST-03",
            "contact_name": "Bullseye Fields", "contact_title": "Treasury Analyst", "contact_phone": "612-555-0300",
            "phone_extension": "303", "email": "unclaimed@property.target.com", "email_confirmation": "unclaimed@property.target.com",
            "address_1": "1000 Nicollet Mall", "address_2": "", "address_3": "", "city": "Minneapolis",
            "state": "MN", "zip_code": "55403", "country": "USA", "state_of_incorporation": "MN",
            "date_of_incorporation": "1902-06-24", "reporting_agent_name": "Target Reporting Services",
            "reporting_agent_fein": "41-0215170", "number_of_employees": 450000,
            "annual_sales_premiums": 90000000, "total_assets": 300000000, "notes": "Sample Target holder.",
            "custom_field_1": "", "custom_field_2": "", "custom_field_3": "", "custom_field_4": "", "custom_field_5": "",
        },
    ]

    df = pd.DataFrame(rows, columns=holder_columns)
    df.to_excel(path, index=False)


def build_filing_workbook(path: Path) -> None:
    filing_columns = [
        "filing_id", "holder_id", "company_name", "state_code", "report_year", "report_type",
        "submission_type", "negative_report", "amount_to_remit", "total_cash_reported",
        "total_dollar_amount_remitted", "total_shares_reported", "total_number_of_properties_reported",
        "total_number_of_owners_reported", "includes_hipaa_records", "includes_safe_deposit_box",
        "funds_remitted_via", "naupa_file_name", "status", "notes",
    ]

    rows = [
        {
            "filing_id": "F-1001", "holder_id": "1", "company_name": "Amazon", "state_code": "CA",
            "report_year": 2025, "report_type": "Annual", "submission_type": "NAUPA Upload",
            "negative_report": False, "amount_to_remit": 1200.50, "total_cash_reported": 1200.50,
            "total_dollar_amount_remitted": 1200.50, "total_shares_reported": 0,
            "total_number_of_properties_reported": 12, "total_number_of_owners_reported": 10,
            "includes_hipaa_records": False, "includes_safe_deposit_box": False,
            "funds_remitted_via": "ACH", "naupa_file_name": "amazon_ca_2025.hde", "status": "pending",
            "notes": "Positive report sample",
        },
        {
            "filing_id": "F-1002", "holder_id": "1", "company_name": "Amazon", "state_code": "CO",
            "report_year": 2025, "report_type": "Annual", "submission_type": "Negative Filing",
            "negative_report": True, "amount_to_remit": 0, "total_cash_reported": 0,
            "total_dollar_amount_remitted": 0, "total_shares_reported": 0,
            "total_number_of_properties_reported": 0, "total_number_of_owners_reported": 0,
            "includes_hipaa_records": False, "includes_safe_deposit_box": False,
            "funds_remitted_via": "N/A", "naupa_file_name": "amazon_co_2025.hde", "status": "pending",
            "notes": "Zero/negative report sample",
        },
        {
            "filing_id": "F-1003", "holder_id": "2", "company_name": "Walmart", "state_code": "AR",
            "report_year": 2025, "report_type": "Annual", "submission_type": "NAUPA Upload",
            "negative_report": False, "amount_to_remit": 300.00, "total_cash_reported": 300.00,
            "total_dollar_amount_remitted": 300.00, "total_shares_reported": 0,
            "total_number_of_properties_reported": 3, "total_number_of_owners_reported": 3,
            "includes_hipaa_records": False, "includes_safe_deposit_box": False,
            "funds_remitted_via": "Wire", "naupa_file_name": "walmart_ar_2025.hde", "status": "in_progress",
            "notes": "Second company sample",
        },
        {
            "filing_id": "F-1004", "holder_id": "3", "company_name": "Target", "state_code": "IL",
            "report_year": 2025, "report_type": "Annual", "submission_type": "NAUPA Upload",
            "negative_report": False, "amount_to_remit": 50.00, "total_cash_reported": 50.00,
            "total_dollar_amount_remitted": 50.00, "total_shares_reported": 0,
            "total_number_of_properties_reported": 1, "total_number_of_owners_reported": 1,
            "includes_hipaa_records": False, "includes_safe_deposit_box": False,
            "funds_remitted_via": "Check", "naupa_file_name": "target_il_2025.hde", "status": "pending",
            "notes": "Third company sample",
        },
    ]

    df = pd.DataFrame(rows, columns=filing_columns)
    df.to_excel(path, index=False)


def main() -> None:
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    build_holder_workbook(SAMPLE_DATA_DIR / "all_holder_information.xlsx")
    build_filing_workbook(SAMPLE_DATA_DIR / "filing_queue.xlsx")
    print("Sample workbooks created in sample_data/")


if __name__ == "__main__":
    main()
