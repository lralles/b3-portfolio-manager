# B3 Portfolio Manager

A Python project for turning B3 investment-account exports into a local,
queryable portfolio data store.

This project is a work in progress. B3's data is spread across exports with
inconsistent formats and semantics, which makes it troublesome to process
reliably. The ingestion code handles the formats and operations currently
needed by the project, but it is not perfect, not finished, and does not yet
support every B3 operation or asset type. 

Feel free to reach out if you use and come accross unsupported operations.
It would be great to expand the capabilities with your input.

## Requirements

- Python 3.11+ (use the repository virtual environment at `.venv/`)
- B3 XLSX exports for transactions and positions

No brokerage credentials are required. The system processes files that have
already been exported from B3.

## Data layout

The `data/` directory is split into three stages:

```text
data/
├── raw/                    # Original B3 exports; never edit these files
│   ├── transactions/       # Transaction XLSX files, recursively discovered
│   └── position/           # Position snapshot XLSX files
├── santized/               # Normalized intermediate CSVs (name kept for compatibility)
│   ├── transactions/       # transactions.csv
│   └── positions/          # source_positions.csv
└── store/                  # Generated application data
    ├── assets/             # Canonical assets
    ├── holdings/           # Institutions
    ├── transactions/       # Normalized transactions
    ├── source_positions/   # Positions as reported by B3
    ├── computed_positions/ # Positions computed from transactions
    ├── profit_losses/      # profit-and-loss output
    └── trading_price/      # Prices used by ingestion and reconciliation
```

The directory is intentionally a sequence of transformations:

```text
B3 XLSX exports → raw → sanitized CSVs → store CSVs → reconciliation checks
```

Raw files are inputs and should remain unchanged so that the pipeline can be
rerun. Sanitized files are generated, normalized representations of those
inputs and are useful for inspecting parsing results. Store files are also
generated and should not be treated as hand-maintained source data.

### What to put in `data/raw`

Put the original B3 XLSX exports in the matching raw directory:

- `data/raw/transactions/`: one or more B3 transaction-history exports. The
  first worksheet must contain the B3 transaction columns such as `Entrada/Saída`,
  `Data`, `Movimentação`, `Produto`, `Instituição`, `Quantidade`,
  `Preço unitário`, and `Valor da Operação`. Files in subdirectories are also
  included.
- `data/raw/position/`: one or more B3 position snapshots. The workbook must
  contain supported worksheets such as `Ações`, `Fundo de investimento`,
  `ETF`, `Renda fixa`, or `Tesouro Direto`. The filename must include the
  evaluation date in this form: `posicao-YYYY-MM-DD.xlsx`.

Use exports from the same account/institution consistently. Do not put the
sanitized CSVs or generated store files in `data/raw`.

## Pipeline

Before running the pipeline, copy `config/config.template.yaml` to
`config/config.yaml` and adjust the paths if needed. The local configuration is
ignored by Git.

```bash
./.venv/bin/python -m src.ingestion.pipeline
```

The complete ingestion pipeline runs these stages in dependency order:

1. Sanitize transaction XLSX files into one normalized transaction CSV.
2. Sanitize position XLSX snapshots into one normalized source-position CSV.
3. Ingest transactions, creating or updating assets, holdings, and
   transactions.
4. Ingest B3 source positions and their supporting assets and prices.
5. Reconcile positions computed from transactions against B3's reported
   positions, producing position and profit/loss outputs.

The pipeline stops if reconciliation reports conflicts. This is deliberate:
the generated store should not silently be treated as correct when the source
exports and transaction history do not agree.

Each stage is also available as a focused module under `src/ingestion/steps/`.
For example, these commands run the two sanitization stages independently:

```bash
./.venv/bin/python -m src.ingestion.steps.step_1_sanitize_transactions
./.venv/bin/python -m src.ingestion.steps.step_2_sanitize_source_positions
```

By default, transaction sanitization reads all XLSX files recursively under
`data/raw/transactions/`. Position sanitization reads all XLSX files
recursively under `data/raw/position/`. The default paths can be overridden in
`config/config.yaml` or with the pipeline's `--raw-transactions`,
`--raw-position`, `--sanitized-dir`, and `--store-dir` options.

The repository uses the directory name `data/santized/` (missing the second
“i”) in its configuration and code. Keep that spelling unless you also update
the configured paths and code references.

## Validation and development

Run the syntax check and, when source exports are available, the full pipeline:

```bash
./.venv/bin/python -m compileall -q src
./.venv/bin/python -m src.ingestion.pipeline
```

The pipeline requires at least one transaction XLSX and one position XLSX
unless the relevant steps are run separately. Generated CSVs are ignored by
Git; keep personal financial exports and generated data out of commits.

Monthly cash-flow analysis is available in `notebooks/monthly_cash_flow.ipynb`.
