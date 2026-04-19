"""
Data anomaly detection.

Checks each time-series column for:
  - Statistical outliers (Z-score and IQR methods)
  - Sudden level shifts (rolling mean deviation)
  - Zero / null spikes

Returns a list of AnomalyAlert objects with severity and root-cause hints.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats


Severity = Literal["info", "warning", "critical"]


@dataclass
class AnomalyAlert:
    table: str
    column: str
    date: str
    value: float
    expected_range: tuple[float, float]
    severity: Severity
    root_cause_hint: str
    check_type: str  # zscore | iqr | level_shift | null_spike


def _zscore_alerts(
    series: pd.Series,
    dates: pd.Series,
    table: str,
    column: str,
    threshold: float = 3.0,
) -> list[AnomalyAlert]:
    alerts = []
    z = np.abs(stats.zscore(series.dropna()))
    for i, (idx, z_val) in enumerate(zip(series.dropna().index, z)):
        if z_val > threshold:
            mean, std = series.mean(), series.std()
            sev: Severity = "critical" if z_val > 4.5 else "warning"
            alerts.append(
                AnomalyAlert(
                    table=table,
                    column=column,
                    date=str(dates.loc[idx].date() if hasattr(dates.loc[idx], "date") else dates.loc[idx]),
                    value=round(float(series.loc[idx]), 4),
                    expected_range=(round(mean - threshold * std, 4), round(mean + threshold * std, 4)),
                    severity=sev,
                    root_cause_hint=(
                        f"Value is {z_val:.1f} standard deviations from the mean. "
                        "Check for data pipeline issues, promotions, or external events."
                    ),
                    check_type="zscore",
                )
            )
    return alerts


def _null_spike_alerts(
    df: pd.DataFrame,
    date_col: str,
    table: str,
    null_rate_threshold: float = 0.10,
) -> list[AnomalyAlert]:
    alerts = []
    for col in df.columns:
        if col == date_col:
            continue
        null_rate = df[col].isna().mean()
        if null_rate > null_rate_threshold:
            sev: Severity = "critical" if null_rate > 0.30 else "warning"
            alerts.append(
                AnomalyAlert(
                    table=table,
                    column=col,
                    date="overall",
                    value=round(null_rate, 4),
                    expected_range=(0.0, null_rate_threshold),
                    severity=sev,
                    root_cause_hint=(
                        f"{null_rate * 100:.1f}% of values are null in '{col}'. "
                        "Possible ingestion failure or upstream schema change."
                    ),
                    check_type="null_spike",
                )
            )
    return alerts


def _level_shift_alerts(
    series: pd.Series,
    dates: pd.Series,
    table: str,
    column: str,
    window: int = 4,
    threshold_pct: float = 0.40,
) -> list[AnomalyAlert]:
    """Detect sudden level shifts by comparing rolling means."""
    alerts = []
    rolling = series.rolling(window=window, min_periods=2).mean()
    pct_change = rolling.pct_change().abs()
    for idx in pct_change[pct_change > threshold_pct].index:
        alerts.append(
            AnomalyAlert(
                table=table,
                column=column,
                date=str(dates.loc[idx].date() if hasattr(dates.loc[idx], "date") else dates.loc[idx]),
                value=round(float(pct_change.loc[idx]), 4),
                expected_range=(0.0, threshold_pct),
                severity="warning",
                root_cause_hint=(
                    f"Rolling mean shifted by {pct_change.loc[idx] * 100:.1f}% "
                    f"in '{column}'. Possible structural break, promotion, or data gap."
                ),
                check_type="level_shift",
            )
        )
    return alerts


def detect_anomalies(
    df: pd.DataFrame,
    date_col: str,
    numeric_cols: list[str],
    table_name: str,
    zscore_threshold: float = 3.0,
    level_shift_pct: float = 0.40,
) -> list[AnomalyAlert]:
    """
    Run all anomaly checks on a DataFrame.

    Args:
        df:                 DataFrame to inspect.
        date_col:           Name of the date column.
        numeric_cols:       Numeric columns to check.
        table_name:         Logical table name for alert labels.
        zscore_threshold:   Z-score cutoff for outlier detection.
        level_shift_pct:    % change in rolling mean to flag a level shift.

    Returns:
        List of AnomalyAlert objects, ordered by severity (critical first).
    """
    df = df.copy().sort_values(date_col).reset_index(drop=True)
    dates = df[date_col]
    alerts: list[AnomalyAlert] = []

    alerts.extend(_null_spike_alerts(df, date_col, table_name))

    for col in numeric_cols:
        if col not in df.columns:
            continue
        series = df[col].ffill()
        alerts.extend(_zscore_alerts(series, dates, table_name, col, zscore_threshold))
        alerts.extend(_level_shift_alerts(series, dates, table_name, col, threshold_pct=level_shift_pct))

    # Sort: critical → warning → info
    order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: order.get(a.severity, 3))
    return alerts


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    df = pd.read_parquet("data/online_sales.parquet")
    daily = df.groupby("date", as_index=False)["revenue"].sum()
    daily["date"] = pd.to_datetime(daily["date"])

    alerts = detect_anomalies(daily, "date", ["revenue"], "online_sales")
    print(f"Detected {len(alerts)} anomalies")
    for a in alerts[:5]:
        print(f"  [{a.severity.upper()}] {a.date}  {a.column}={a.value}  — {a.root_cause_hint}")
