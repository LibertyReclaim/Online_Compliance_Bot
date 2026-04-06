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
├── Amazon/
│   ├── CA.txt
│   └── NY.txt
│
├── Walmart/
│   └── CA.txt
│
└── README.md
```

## Required Setup

Before running the bot, you must manually create these Excel files in the **project root**:

1. `all_holder_information.xlsx`
2. `filing_execution.xlsx`

The project **does not generate Excel files automatically**.

### Required columns: all_holder_information.xlsx

- `holder_id`
- `company_name`
- `holder_name`
- `contact_name`
- `contact_phone`
- `email`

### Required columns: filing_execution.xlsx

- `filing_id`
- `holder_id`
- `company_name`
- `state_code`
- `amount_to_remit`
- `naupa_file_name`
- `status`

If either workbook is missing, the bot raises a clear error message such as:

`Missing required file: all_holder_information.xlsx. Please create it manually.`

## NAUPA / file location rule

NAUPA files are stored directly inside each company folder at project root.

Example resolution:
- `company_name = Amazon`
- `naupa_file_name = CA.txt`
- resolved path: `Online_Compliance_Bot/Amazon/CA.txt`

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
