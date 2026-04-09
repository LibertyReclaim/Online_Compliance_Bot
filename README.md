# Online Compliance Bot

## Project Structure

```
Online_Compliance_Bot/
│
├── code/
│   ├── main.py
│   ├── config.py
│   ├── excel_loader.py
│   ├── path_utils.py
│   ├── state_registry.py
│   ├── utils.py
│   ├── models.py
│   ├── validation.py
│   └── states/
│       ├── __init__.py
│       ├── base_state.py
│       ├── alabama.py
│       ├── alaska.py
│       ├── arkansas.py
│       ├── california.py
│       ├── colorado.py
│       ├── connecticut.py
│       ├── delaware.py
│       ├── idaho.py
│       ├── illinois.py
│       └── indiana.py
│
├── holder_information.xlsx   # create manually
├── payment_file.xlsx         # create manually
│
├── Amazon/
│   ├── CA.txt
│   └── NY.txt
│
└── Walmart/
    └── CA.txt
```

## Two-workbook model

The bot uses two manually maintained workbooks in the project root:

1. `holder_information.xlsx`
   - Master holder/company data reused across filings.
   - Match key: `holder_id`.

2. `payment_file.xlsx`
   - Execution queue; each row is one state filing/payment run.
   - Blank until your team is ready to execute filings.

The repository does **not** generate workbook files automatically.

## Required columns

### holder_information.xlsx (minimum required)

- `holder_id`
- `company_name`
- `holder_name`
- `holder_tax_id`
- `holder_id_secondary`
- `contact_name`
- `contact_phone`
- `phone_extension`
- `email`
- `email_confirmation`
- `address_1`
- `address_2`
- `city`
- `state`
- `zip`
- `country`

> You can add additional holder columns as new state workflows require them.

### payment_file.xlsx (minimum required)

- `payment_id`
- `holder_id`
- `company_name`
- `state_code`
- `amount_to_remit`
- `funds_remitted_via`
- `report_year`
- `report_type`
- `naupa_file_name`
- `status`
- `notes`

> You can add additional payment columns later for state-specific needs.

## Workflow

1. Read `payment_file.xlsx`.
2. For each row, match `holder_id` to `holder_information.xlsx`.
3. Determine report type:
   - `amount_to_remit == 0` → negative report
   - `amount_to_remit > 0` → positive report
4. Load state runner from `code/states/`.
5. Resolve NAUPA file path from root company folder:
   - `PROJECT_ROOT / company_name / naupa_file_name`
   - Example: `PROJECT_ROOT / "Amazon" / "NY.txt"`
6. Execute state-specific logic.

## Validation behavior

- Missing `holder_information.xlsx` → clear error.
- Missing `payment_file.xlsx` → clear error.
- Unknown `holder_id` in payment row → clear error.
- Missing NAUPA file in company folder → clear error.

## How to run

From repository root:

```bash
cd code
py main.py --company Amazon
```

Other examples:

```bash
cd code
py main.py
py main.py --state CA
py main.py --holder-id 1
py main.py --status pending
```

## Add more states

1. Add a new module under `code/states/`.
2. Expose `run_<state>(context, company_data, filing_data)`.
3. Register it in `code/state_registry.py`.
4. Add the state code to `SUPPORTED_STATES` in `code/config.py`.

This keeps the scaffold modular so state-specific logic can be plugged in incrementally.
