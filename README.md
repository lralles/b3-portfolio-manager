# B3 Portfolio Manager

A small Python project for processing B3 portfolio data.

## Pipeline

```bash
./.venv/bin/python -m src.ingestion.pipeline
```

The pipeline runs sanitization (transactions and source positions), ingestion
(transactions, holdings, and assets), and quality checks (source-position
ingestion and position reconciliation) in dependency order. Each step is also
available as its own module under `src/ingestion` for focused runs.

Source-position ingestion uses only `data/raw/position/2020/posicao-2020-12-31.xlsx`
by default. The sanitized CSV is written under `data/santized/positions/`, and the
stored model is written to `data/store/source_positions/source_positions.csv`.

Monthly cash-flow analysis is available in `notebooks/monthly_cash_flow.ipynb`.
