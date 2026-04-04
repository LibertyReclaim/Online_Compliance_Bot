# Online Compliance Bot

A modular Python 3.11+ scaffold for automating multi-state unclaimed property reporting with Playwright.

## Purpose

This project is designed for shared team usage (including shared OneDrive folders). It reads:

1. `sample_data/all_holder_information.xlsx` (holder master data)
2. `sample_data/filing_queue.xlsx` (filing execution queue)

Then it matches each filing by `holder_id`, resolves the expected NAUPA file path, and calls a state-specific module in `states/`.

## Folder Structure

```
Online_Compliance_Bot/
├── main.py
├── config.py
├── path_utils.py
├── excel_loader.py
├── models.py
├── validation.py
├── logging_utils.py
├── state_registry.py
├── create_sample_workbooks.py
├── requirements.txt
├── README.md
├── .gitignore
├── sample_data/
│   ├── all_holder_information.xlsx
│   └── filing_queue.xlsx
├── states/
│   ├── __init__.py
│   ├── base_state.py
│   ├── alabama.py
│   ├── alaska.py
│   ├── arkansas.py
│   ├── california.py
│   ├── colorado.py
│   ├── connecticut.py
│   ├── delaware.py
│   ├── idaho.py
│   ├── illinois.py
│   └── indiana.py
└── clients/
    └── Amazon/
        ├── AL/
        ├── AK/
        ├── AR/
        ├── CA/
        ├── CO/
        ├── CT/
        ├── DE/
        ├── ID/
        ├── IL/
        └── IN/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install
```

## Create / Refresh Sample Excel Workbooks

```bash
python create_sample_workbooks.py
```

The generated workbooks include:
- Holder master rows for Amazon, Walmart, and Target.
- Filing queue rows including positive and negative (amount `0`) examples.
- Multiple states for one company.

## How NAUPA File Resolution Works

For each filing row, the bot builds:

`clients/<company_name>/<state_code>/<naupa_file_name>`

Example:

`clients/Amazon/CA/amazon_ca_2025.hde`

## Run the Bot

```bash
python main.py
python main.py --state CA
python main.py --holder-id 1
python main.py --company Amazon
python main.py --status pending
python main.py --status pending --state CO --headless
```

## Adding a New State Module

1. Add a new state file in `states/` (for example `florida.py`).
2. Add a runner function in that file (for example `run_florida(context, company_data, filing_data)`).
3. Register the module/function mapping in `state_registry.py`.
4. Add the state abbreviation to `SUPPORTED_STATES` in `config.py`.
5. Create client folders as needed under `clients/<Company>/<STATE>/`.

## Notes on State Flexibility

Each state module is intentionally a stub with TODO steps:
- open page
- fill holder information
- fill report information
- upload NAUPA file
- return status

This keeps the scaffold stable while allowing each state team member to paste in custom Playwright logic.
