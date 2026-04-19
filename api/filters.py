"""
Filter helpers and reliability warnings.

Provides a shared FilterParams model used by all dashboard endpoints,
plus logic to warn when the selected filter combination reduces statistical
reliability or model confidence.
"""
from __future__ import annotations

from typing import Optional
import pandas as pd
from pydantic import BaseModel, model_validator


# Minimum rows below which we emit a reliability warning
MIN_ROWS_WARNING = 30


class FilterParams(BaseModel):
    start_date:   Optional[str] = None
    end_date:     Optional[str] = None
    channel:      Optional[str] = None     # e.g. "DTC", "Amazon", "Paid Search"
    category:     Optional[str] = None     # e.g. "Beverages"
    region:       Optional[str] = None     # e.g. "Northeast"
    store_format: Optional[str] = None     # e.g. "Supermarket"
    industry:     Optional[str] = None     # CRM funnel industry
    lead_source:  Optional[str] = None     # CRM lead source


def apply_date_filter(
    df: pd.DataFrame,
    date_col: str,
    params: FilterParams,
) -> pd.DataFrame:
    if params.start_date:
        df = df[df[date_col] >= pd.Timestamp(params.start_date)]
    if params.end_date:
        df = df[df[date_col] <= pd.Timestamp(params.end_date)]
    return df


def apply_filters(
    df: pd.DataFrame,
    date_col: str,
    params: FilterParams,
    col_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Apply all relevant filter params to a DataFrame.

    col_map lets callers alias param names to actual column names
    e.g. {"channel": "lead_source"} for the CRM funnel table.
    """
    col_map = col_map or {}
    df = apply_date_filter(df, date_col, params)

    for param_name in ["channel", "category", "region", "store_format", "industry", "lead_source"]:
        value = getattr(params, param_name, None)
        if value is None:
            continue
        actual_col = col_map.get(param_name, param_name)
        if actual_col in df.columns:
            df = df[df[actual_col] == value]

    return df


def reliability_warning(df: pd.DataFrame, context: str = "") -> str | None:
    """
    Return a warning string if the filtered DataFrame is too small
    for reliable statistics or modeling.
    """
    n = len(df)
    if n == 0:
        return f"No data matches the selected filters{f' ({context})' if context else ''}."
    if n < MIN_ROWS_WARNING:
        return (
            f"Only {n} rows match the selected filters{f' ({context})' if context else ''}. "
            "Statistics and model outputs may be unreliable with fewer than 30 data points. "
            "Consider broadening your date range or removing dimension filters."
        )
    return None
