"""Backward-compatible entry point for the split ingestion steps."""

from src.ingestion.steps.step_3_ingest_transactions import main


if __name__ == "__main__":
    raise SystemExit(main())
