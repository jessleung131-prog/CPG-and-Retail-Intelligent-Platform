"""
Marketing Mix Model (MMM) — channel contribution and incremental ROI.

Uses a Ridge regression approach with:
  - Adstock (geometric carryover) transform per channel
  - Hill saturation (diminishing returns) per channel
  - Chronological train/val/test split (no data leakage)

Outputs:
  - Channel contribution % to total sales
  - Incremental revenue per channel
  - Incremental ROI per channel (revenue / spend)
  - Sales decomposition: base sales vs media-driven vs promotions
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler


MEDIA_CHANNELS = [
    "Paid Search",
    "Paid Social",
    "Display",
    "TV / CTV",
    "Email",
    "Influencer",
]


@dataclass
class MMMResult:
    model_name: str = "Ridge MMM"
    metrics: dict[str, float] = None          # r2, rmse, mape on validation
    channel_contributions: pd.DataFrame = None # channel, contribution_pct, incremental_rev, roi
    decomposition: pd.DataFrame = None         # week, base_sales, promo_sales, media_sales, total
    coefficients: dict[str, float] = None      # raw model coefficients
    confidence_warning: str | None = None


def _adstock(series: np.ndarray, decay: float) -> np.ndarray:
    out = np.zeros_like(series, dtype=float)
    for t in range(len(series)):
        out[t] = series[t] + (out[t - 1] * decay if t > 0 else 0)
    return out


def _hill_saturation(x: np.ndarray, k: float = 0.0001) -> np.ndarray:
    return x / (1 + k * x)


def _prepare_features(
    media_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    date_col: str = "week_start",
    sales_col: str = "total_revenue",
    adstock_decay: float = 0.40,
    saturation_k: float = 0.00005,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Join media spend to sales, apply adstock + saturation transforms,
    and add calendar features.
    """
    # Pivot media spend wide: one column per channel
    spend_wide = media_df.pivot_table(
        index=date_col, columns="channel", values="spend", aggfunc="sum"
    ).reset_index()

    # Aggregate sales to weekly
    sales_agg = (
        sales_df.copy()
        .assign(**{date_col: lambda d: pd.to_datetime(d[date_col])})
        .groupby(date_col)[sales_col]
        .sum()
        .reset_index()
    )

    df = spend_wide.merge(sales_agg, on=date_col, how="inner")
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    # Apply adstock + saturation to each channel
    for ch in MEDIA_CHANNELS:
        if ch not in df.columns:
            df[ch] = 0.0
        raw = df[ch].values
        adstocked = _adstock(raw, adstock_decay)
        df[f"{ch}_transformed"] = _hill_saturation(adstocked, saturation_k)

    # Calendar features
    df["week_of_year"] = df[date_col].dt.isocalendar().week.astype(int)
    df["sin_week"] = np.sin(2 * np.pi * df["week_of_year"] / 52)
    df["cos_week"] = np.cos(2 * np.pi * df["week_of_year"] / 52)
    df["trend"]    = np.arange(len(df)) / len(df)

    transformed_cols = [f"{ch}_transformed" for ch in MEDIA_CHANNELS]
    calendar_cols    = ["sin_week", "cos_week", "trend"]
    feature_cols     = transformed_cols + calendar_cols

    X = df[feature_cols]
    y = df[sales_col]

    return df, X, y, feature_cols


def run_mmm(
    media_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    date_col: str = "week_start",
    sales_col: str = "total_revenue",
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> MMMResult:
    """
    Fit a Marketing Mix Model on weekly media spend + sales.

    Args:
        media_df:   Media spend DataFrame with columns [week_start, channel, spend].
        sales_df:   Sales DataFrame with columns [week_start, total_revenue].
        date_col:   Date column name.
        sales_col:  Revenue column name.
        train_frac: Training fraction of time range.
        val_frac:   Validation fraction.

    Returns:
        MMMResult with channel contributions, decomposition, and metrics.
    """
    from models.splitter import split

    df, X, y, feature_cols = _prepare_features(
        media_df, sales_df, date_col, sales_col
    )

    # Chronological split
    splits = split(df, date_col, train_frac=train_frac, val_frac=val_frac)
    train_idx = df[date_col] <= pd.Timestamp(splits.train_end)
    val_idx   = (df[date_col] > pd.Timestamp(splits.train_end)) & \
                (df[date_col] <= pd.Timestamp(splits.val_end))

    X_train, y_train = X[train_idx], y[train_idx]
    X_val,   y_val   = X[val_idx],   y[val_idx]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s   = scaler.transform(X_val)
    X_all_s   = scaler.transform(X)

    model = Ridge(alpha=1.0, positive=True)
    model.fit(X_train_s, y_train)

    # Validation metrics
    y_pred_val = model.predict(X_val_s)
    r2   = float(r2_score(y_val, y_pred_val))
    rmse = float(np.sqrt(np.mean((y_val.values - y_pred_val) ** 2)))
    nonzero = y_val.values != 0
    mape = float(np.mean(np.abs((y_val.values[nonzero] - y_pred_val[nonzero]) / y_val.values[nonzero])) * 100)

    metrics = {"r2": round(r2, 4), "rmse": round(rmse, 2), "mape": round(mape, 3)}

    # Full-sample predictions for decomposition
    y_all_pred = model.predict(X_all_s)
    coef = dict(zip(feature_cols, model.coef_))

    # Channel contribution: attribution via coefficient * scaled feature mean
    X_all_arr = scaler.transform(X)
    transformed_cols = [f"{ch}_transformed" for ch in MEDIA_CHANNELS]
    calendar_cols    = ["sin_week", "cos_week", "trend"]

    media_contributions = {}
    for ch in MEDIA_CHANNELS:
        col = f"{ch}_transformed"
        col_idx = feature_cols.index(col)
        media_contributions[ch] = (
            model.coef_[col_idx] * X_all_arr[:, col_idx]
        ).mean()

    total_media = sum(media_contributions.values())
    total_pred  = y_all_pred.mean()

    channel_rows = []
    for ch in MEDIA_CHANNELS:
        contrib_pct = media_contributions[ch] / max(total_pred, 1) * 100
        incr_rev = media_contributions[ch] * len(df)
        spend_total = media_df[media_df["channel"] == ch]["spend"].sum()
        roi = incr_rev / max(spend_total, 1)
        channel_rows.append({
            "channel": ch,
            "contribution_pct": round(contrib_pct, 2),
            "incremental_revenue": round(incr_rev, 0),
            "total_spend": round(spend_total, 0),
            "incremental_roi": round(roi, 3),
        })

    channel_df = pd.DataFrame(channel_rows).sort_values(
        "contribution_pct", ascending=False
    ).reset_index(drop=True)

    # Sales decomposition
    base_pred = model.intercept_
    calendar_idx = [feature_cols.index(c) for c in calendar_cols]
    calendar_contrib = sum(
        model.coef_[i] * X_all_arr[:, i] for i in calendar_idx
    )
    media_contrib_total = np.array([
        model.coef_[feature_cols.index(f"{ch}_transformed")] * X_all_arr[:, feature_cols.index(f"{ch}_transformed")]
        for ch in MEDIA_CHANNELS
    ]).sum(axis=0)

    decomp_df = pd.DataFrame({
        "week_start": df[date_col].values,
        "base_sales":  base_pred + calendar_contrib,
        "media_sales": media_contrib_total,
        "total_predicted": y_all_pred,
        "actual_sales": y.values,
    })

    warning = None
    if mape > 25:
        warning = f"MMM validation MAPE is {mape:.1f}%. Channel contributions have high uncertainty — use for directional guidance only."
    elif r2 < 0.50:
        warning = f"Low R² ({r2:.2f}). The model may be missing important drivers. Interpret contributions with caution."

    return MMMResult(
        metrics=metrics,
        channel_contributions=channel_df,
        decomposition=decomp_df,
        coefficients={k: round(v, 6) for k, v in coef.items()},
        confidence_warning=warning,
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    media_path = Path("data/media_spend.parquet")
    sales_path = Path("data/offline_sales.parquet")

    if not media_path.exists() or not sales_path.exists():
        print("Run synthetic_data/generate_all.py first.")
        sys.exit(1)

    media_df = pd.read_parquet(media_path)
    sales_df = (
        pd.read_parquet(sales_path)
        .groupby("week_start", as_index=False)["total_revenue"]
        .sum()
    )

    result = run_mmm(media_df, sales_df)
    print(f"R²: {result.metrics['r2']}   MAPE: {result.metrics['mape']}%")
    print(f"\nChannel contributions:\n{result.channel_contributions}")
    if result.confidence_warning:
        print(f"\nWARNING: {result.confidence_warning}")
