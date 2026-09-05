# Repository Guidelines

## Project Structure & Module Organization

- `src/core/models/` contains typed domain models for accounts, assets, and transactions.
- `src/core/repositories/` provides persistence access, currently via stored CSV files.
- `src/core/services/` contains business logic such as monthly cash-flow calculations.
- `src/ingestion/` contains command-line scripts that sanitize XLSX exports and format them into the store model.
- `data/raw/` holds source exports; `data/santized/` holds normalized intermediate data; `data/store/` holds generated CSV data.
- `notebooks/` contains exploratory analysis. There is currently no dedicated test suite.

Keep raw and generated financial data out of commits unless explicitly required; CSV/XLSX files are ignored by default.

## Build, Test, and Development Commands

Use the repository virtual environment:

```bash
./.venv/bin/python -m compileall -q src
./.venv/bin/python -m src.ingestion.sanitize_transactions
./.venv/bin/python -m src.ingestion.format_transactions
```

The first command checks Python syntax. The ingestion commands convert XLSX files under `data/raw/transactions/` into sanitized and stored CSVs using their default paths. Override paths with `--raw-dir`, `--input`, or `--output` when needed.

## Coding Style & Naming Conventions

Write Python with 4-space indentation, type annotations, and `from __future__ import annotations` for new modules. Use `snake_case` for functions, variables, and modules; `PascalCase` for classes; and uppercase names for constants. Prefer immutable dataclasses for domain values, `Decimal` for monetary values, and explicit exceptions for invalid input. Keep imports grouped and avoid adding runtime dependencies without documenting them.

## Testing Guidelines

No test framework or coverage threshold is configured yet. Keep tests close to the implementation they cover, colocated in the relevant `src/` package, and name files `*_test.py` (for example, `src/core/services/build_position_test.py`). Cover parsing, validation, cash-flow classification, and month-boundary behavior. At minimum, run compilation and the relevant ingestion command before submitting changes.

## Commit & Pull Request Guidelines

Existing commits use short, imperative-style prefixes such as `feat:` and `chore:` (for example, `feat: add transaction processing`). Follow that convention with a concise subject. Pull requests should explain the data-flow or model change, list validation commands run, identify affected input/output paths, and call out any schema or generated-data changes. Never include credentials or unreviewed personal financial exports.

## Data and Notebook Hygiene

Do not commit secrets, raw brokerage exports, or unnecessary notebook outputs. The pre-commit hook clears Jupyter outputs for staged notebooks; install or enable it through the repository’s Git hooks configuration before committing notebook changes.
