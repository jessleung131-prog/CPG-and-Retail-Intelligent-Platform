"""
Load synthetic (or real) Parquet files into BigQuery raw layer.

Supports:
  - Full load (truncate + reload)
  - Incremental load (append rows newer than last ingested date)

Usage:
    # Full load all tables
    python ingestion/load_to_bigquery.py --mode full

    # Incremental load (append new rows only)
    python ingestion/load_to_bigquery.py --mode incremental
"""
import argparse
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from google.cloud import bigquery

from config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Map: table_name → (parquet_file, date_column_for_incremental)
TABLE_CONFIG = {
    "online_sales":  ("online_sales.parquet",  "date"),
    "offline_sales": ("offline_sales.parquet", "week_start"),
    "crm_funnel":    ("crm_funnel.parquet",    "lead_date"),
    "media_spend":   ("media_spend.parquet",   "week_start"),
}


def _get_max_date(client: bigquery.Client, table_ref: str, date_col: str) -> str | None:
    """Return the maximum date already in a BQ table, or None if empty."""
    try:
        result = client.query(
            f"SELECT MAX({date_col}) AS max_date FROM `{table_ref}`"
        ).result()
        row = next(iter(result), None)
        if row and row.max_date:
            return str(row.max_date)
    except Exception:
        pass
    return None


def _log_pipeline_run(
    client: bigquery.Client,
    table_name: str,
    rows: int,
    status: str,
    error: str,
    duration: float,
):
    run_id = str(uuid.uuid4())
    monitoring_table = (
        f"{settings.gcp_project_id}.{settings.bq_dataset_monitoring}.pipeline_runs"
    )
    rows_to_insert = [
        {
            "run_id": run_id,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "table_name": table_name,
            "rows_ingested": rows,
            "status": status,
            "error_message": error or "",
            "duration_secs": round(duration, 2),
        }
    ]
    try:
        client.insert_rows_json(monitoring_table, rows_to_insert)
    except Exception:
        pass  # Don't let monitoring failure block data load


def load_table(
    client: bigquery.Client,
    table_name: str,
    parquet_file: str,
    date_col: str,
    mode: str,
):
    t0 = time.time()
    path = DATA_DIR / parquet_file
    if not path.exists():
        print(f"  [SKIP] {parquet_file} not found — run synthetic_data/generate_all.py first")
        return

    df = pd.read_parquet(path)
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()

    table_ref = f"{settings.gcp_project_id}.{settings.bq_dataset_raw}.{table_name}"

    if mode == "incremental":
        max_date = _get_max_date(client, table_ref, date_col)
        if max_date:
            df[date_col] = pd.to_datetime(df[date_col]).dt.date
            df = df[df[date_col] > pd.to_datetime(max_date).date()]
            if df.empty:
                print(f"  [{table_name}] No new rows since {max_date} — skipping")
                return

    write_disposition = (
        bigquery.WriteDisposition.WRITE_TRUNCATE
        if mode == "full"
        else bigquery.WriteDisposition.WRITE_APPEND
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
        autodetect=False,
    )

    try:
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        duration = time.time() - t0
        print(f"  [{table_name}] Loaded {len(df):,} rows → {table_ref}  ({duration:.1f}s)")
        _log_pipeline_run(client, table_name, len(df), "success", None, duration)
    except Exception as e:
        duration = time.time() - t0
        print(f"  [{table_name}] ERROR: {e}")
        _log_pipeline_run(client, table_name, 0, "failed", str(e), duration)


def main(mode: str = "full"):
    client = bigquery.Client(project=settings.gcp_project_id)
    print(f"Mode: {mode}  |  Project: {settings.gcp_project_id}\n")
    for table_name, (parquet_file, date_col) in TABLE_CONFIG.items():
        load_table(client, table_name, parquet_file, date_col, mode)
    print("\nIngestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    args = parser.parse_args()
    main(args.mode)
