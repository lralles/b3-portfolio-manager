"""Backward-compatible entry point for source-position quality ingestion."""

from src.ingestion.steps.step_4_ingest_source_positions import main


if __name__ == "__main__":
    raise SystemExit(main())
