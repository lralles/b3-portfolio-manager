# B3 Portfolio Manager

A small Python project for processing B3 portfolio data.

## Commands

```bash
./.venv/bin/python -m src.ingestion.sanitize_transactions
./.venv/bin/python -m src.ingestion.format_transactions
./.venv/bin/python -m src.ingestion.sanitize_source_positions
./.venv/bin/python -m src.ingestion.format_source_positions
```

Source-position ingestion uses only `data/raw/position/2020/posicao-2020-12-31.xlsx`
by default. The sanitized CSV is written under `data/santized/positions/`, and the
stored model is written to `data/store/source_positions/source_positions.csv`.

Monthly cash-flow analysis is available in `notebooks/monthly_cash_flow.ipynb`.
