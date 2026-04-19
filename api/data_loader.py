"""
Data loader for API layer.

Loads from local Parquet files (dev mode) or BigQuery (production).
All API route handlers call through this module — never read files directly.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _parquet(name: str) -> pd.DataFrame:
    path = DATA_DIR / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}. "
            "Run `python synthetic_data/generate_all.py` to generate synthetic data."
        )
    return pd.read_parquet(path)


@lru_cache(maxsize=4)
def load_online_sales() -> pd.DataFrame:
    df = _parquet("online_sales")
    df["date"] = pd.to_datetime(df["date"])
    return df


@lru_cache(maxsize=4)
def load_offline_sales() -> pd.DataFrame:
    df = _parquet("offline_sales")
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df


@lru_cache(maxsize=4)
def load_crm_funnel() -> pd.DataFrame:
    df = _parquet("crm_funnel")
    for col in ["lead_date", "mql_date", "sql_date", "opportunity_date", "close_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


@lru_cache(maxsize=4)
def load_media_spend() -> pd.DataFrame:
    df = _parquet("media_spend")
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df


def clear_cache():
    """Force reload on next access — call after new data is ingested."""
    load_online_sales.cache_clear()
    load_offline_sales.cache_clear()
    load_crm_funnel.cache_clear()
    load_media_spend.cache_clear()
