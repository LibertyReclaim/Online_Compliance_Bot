# Online Compliance Bot

## Final Repository Structure

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
│       └── __init__.py
│
├── state_payment_guides/
│   └── .gitkeep
│
├── Amazon/
├── Walmart/
│
└── README.md
```

## Key Rules

- All Python code lives under `code/`.
- Future state modules will be added under `code/states/` one by one and tested one by one.
- No root-level Python files are used.
- No `clients/`, `sample_data/`, or root `states/` folders are used.
- No `.xlsx` files are included in this repository.

## Manual workbook setup (required)

You must create these files manually in the project root before running:

1. `holder_information.xlsx`
2. `payment_file.xlsx`

The bot expects them at:

- `PROJECT_ROOT / "holder_information.xlsx"`
- `PROJECT_ROOT / "payment_file.xlsx"`

## Company folders and NAUPA files

Company folders live directly in the project root (for example `Amazon/`, `Walmart/`).

NAUPA files are loaded from:

- `PROJECT_ROOT / company_name / naupa_file_name`

Example:

- `PROJECT_ROOT / "Amazon" / "NY.txt"`

## state_payment_guides/

`state_payment_guides/` is reserved for one guide file per state.
Each guide will describe extra payment fields required for that state beyond shared holder fields.

## Running the bot

From repository root:

```bash
cd code
py main.py --company Amazon
```

## State registry status

`code/state_registry.py` is intentionally a placeholder with an empty registry until individual state modules are added.
