# Watchbill CDS7

WATCHBILL_CDS7 is a Python-based tool for managing, generating, and evaluating organizational watchbills. It automates the assignment of day and night watches, tracks personnel availability, and enforces custom rules and constraints (such as leave, special liberty, and fair distribution of watches). The project integrates with Excel workbooks for data input and output, and provides utilities for analyzing watch statistics, generating monthly duty vectors, and ensuring compliance with operational requirements.

A Python project for managing watchbills.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

- `src/` - Source code directory
- `tests/` - Test files
- `requirements.txt` - Project dependencies
- `README.md` - Project documentation

## Development

To start development, activate the virtual environment and install the development dependencies:

```bash
pip install -r requirements-dev.txt
``` 
