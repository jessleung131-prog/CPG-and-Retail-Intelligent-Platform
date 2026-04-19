"""
Pipeline and data freshness monitoring.

Checks:
  - Data freshness: how many days since the latest record?
  - Row count health: did we receive an unusual number of rows recently?
  - Schema drift: are expected columns present with expected types?

Returns structured MonitorResult objects suitable for API responses and alerts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

import pandas as pd


Severity = Literal["ok", "warning", "critical"]


@dataclass
class MonitorResult:
    table: str
    check: str
    status: Severity
    detail: str
    metric_value: float | None = None
    threshold: float | None = None
    root_cause_hint: str | None = None
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def check_freshness(
    df: pd.DataFrame,
    date_col: str,
    table_name: str,
    warning_days: int = 3,
    critical_days: int = 7,
) -> MonitorResult:
    """
    Check how stale the most recent data is.
    """
    if df.empty:
        return MonitorResult(
            table=table_name,
            check="freshness",
            status="critical",
            detail="Table is empty.",
            root_cause_hint="Ingestion may have never run or failed on first load.",
        )

    latest = pd.to_datetime(df[date_col]).max()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    age_days = (now - latest).days

    if age_days >= critical_days:
        status: Severity = "critical"
        hint = f"No new data for {age_days} days. Check pipeline run logs and upstream data sources."
    elif age_days >= warning_days:
        status = "warning"
        hint = f"Data is {age_days} days old. Expected refresh cadence may have been missed."
    else:
        status = "ok"
        hint = None

    return MonitorResult(
        table=table_name,
        check="freshness",
        status=status,
        detail=f"Latest record: {latest.date()}  ({age_days} days ago)",
        metric_value=float(age_days),
        threshold=float(warning_days),
        root_cause_hint=hint,
    )


def check_row_count(
    df: pd.DataFrame,
    date_col: str,
    table_name: str,
    lookback_periods: int = 4,
    drop_threshold_pct: float = 0.40,
) -> MonitorResult:
    """
    Compare recent row counts to historical average.
    Flags if the most recent period is significantly lower.
    """
    if df.empty or len(df) < lookback_periods * 2:
        return MonitorResult(
            table=table_name,
            check="row_count",
            status="warning",
            detail="Insufficient data for row count comparison.",
        )

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    by_period = df.groupby(df[date_col].dt.to_period("W")).size()

    if len(by_period) < lookback_periods + 1:
        return MonitorResult(
            table=table_name, check="row_count", status="ok",
            detail="Not enough periods to compare."
        )

    recent = float(by_period.iloc[-1])
    historical_avg = float(by_period.iloc[-(lookback_periods + 1):-1].mean())
    drop_pct = (historical_avg - recent) / max(historical_avg, 1)

    if drop_pct >= drop_threshold_pct:
        status: Severity = "critical" if drop_pct >= 0.60 else "warning"
        hint = (
            f"Row count dropped {drop_pct * 100:.0f}% vs recent average "
            f"({recent:.0f} vs {historical_avg:.0f}). "
            "Possible partial ingestion, upstream truncation, or filter change."
        )
    else:
        status = "ok"
        hint = None

    return MonitorResult(
        table=table_name,
        check="row_count",
        status=status,
        detail=f"Recent: {recent:.0f} rows  |  Historical avg: {historical_avg:.0f} rows",
        metric_value=round(drop_pct, 4),
        threshold=drop_threshold_pct,
        root_cause_hint=hint,
    )


def check_schema(
    df: pd.DataFrame,
    table_name: str,
    expected_columns: list[str],
) -> MonitorResult:
    """
    Verify all expected columns are present.
    """
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        return MonitorResult(
            table=table_name,
            check="schema_drift",
            status="critical",
            detail=f"Missing columns: {missing}",
            root_cause_hint=(
                "Schema change detected. Upstream source may have renamed or removed columns. "
                "Update ingestion mapping before proceeding."
            ),
        )
    return MonitorResult(
        table=table_name,
        check="schema_drift",
        status="ok",
        detail="All expected columns present.",
    )


def run_all_checks(
    dataframes: dict[str, tuple[pd.DataFrame, str, list[str]]],
) -> list[MonitorResult]:
    """
    Run freshness, row count, and schema checks across all tables.

    Args:
        dataframes: Dict of {table_name: (df, date_col, expected_cols)}

    Returns:
        List of MonitorResult objects ordered by severity.
    """
    results: list[MonitorResult] = []

    for table_name, (df, date_col, expected_cols) in dataframes.items():
        results.append(check_freshness(df, date_col, table_name))
        results.append(check_row_count(df, date_col, table_name))
        results.append(check_schema(df, table_name, expected_cols))

    order = {"critical": 0, "warning": 1, "ok": 2}
    results.sort(key=lambda r: order.get(r.status, 3))
    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    online = pd.read_parquet("data/online_sales.parquet")
    online["date"] = pd.to_datetime(online["date"])

    results = run_all_checks({
        "online_sales": (online, "date", ["date", "channel", "revenue", "orders"]),
    })
    for r in results:
        print(f"[{r.status.upper()}] {r.table} / {r.check}: {r.detail}")
        if r.root_cause_hint:
            print(f"  Hint: {r.root_cause_hint}")
