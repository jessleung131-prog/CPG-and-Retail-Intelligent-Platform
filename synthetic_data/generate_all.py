"""
Master synthetic data generator.

Runs all four data streams and saves output to data/ as Parquet files.

Causal design: offline_sales weekly totals are generated using the same
generative model that the Ridge MMM assumes (base + sinusoidal seasonality
+ linear trend + Σ channel_contribution), guaranteeing the MMM can recover
meaningful channel attributions with positive validation R².  The detailed
per-region / per-format / per-category breakdown is preserved by distributing
the MMM-derived weekly totals proportionally across all rows.

Usage:
    python synthetic_data/generate_all.py

Output files:
    data/online_sales.parquet
    data/offline_sales.parquet
    data/crm_funnel.parquet
    data/media_spend.parquet
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synthetic_data import online_sales, offline_sales, crm_funnel, media_spend, account_revenue
from config import settings

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"

# ── Ground-truth channel coefficients (revenue per unit of adstock) ──────────
# These represent the "true" ROAS that the MMM will approximately recover.
CHANNEL_TRUE_COEF = {
    "Paid Search":          3.50,
    "Facebook / Instagram": 2.40,
    "TikTok":               1.80,
    "Reddit":               1.50,
    "Display":              1.20,
    "TV / CTV":             1.60,
    "Email":               10.00,   # highest ROAS — low spend but very efficient
    "Influencer":           1.90,
}

# Adstock decay used for the ground-truth data generation — must match
# adstock_decay in models/mmm._prepare_features (default 0.40).
MMM_ADSTOCK_DECAY = 0.40


def _adstock(series: np.ndarray, decay: float) -> np.ndarray:
    out = np.zeros_like(series, dtype=float)
    for t in range(len(series)):
        out[t] = series[t] + (out[t - 1] * decay if t > 0 else 0)
    return out


def _build_true_weekly_sales(
    media_df: pd.DataFrame,
    weeks: pd.DatetimeIndex,
    seed: int,
) -> np.ndarray:
    """
    Generate weekly offline revenue using the MMM's generative model:

        y[t] = intercept
              + A * sin(2π * week_of_year / 52)
              + B * cos(2π * week_of_year / 52)
              + C * trend[t]
              + Σ_ch  coef_ch * adstock(spend_ch)[t]
              + ε[t]

    Parameters are chosen to give a realistic CPG revenue scale (~$400–700k/wk)
    with media explaining roughly 30 % of total weekly variance.
    """
    rng = np.random.default_rng(seed)
    n = len(weeks)

    # Calendar components (same features as models/mmm._prepare_features)
    week_of_year = pd.DatetimeIndex(weeks).isocalendar().week.astype(int).values
    sin_w = np.sin(2 * np.pi * week_of_year / 52)
    cos_w = np.cos(2 * np.pi * week_of_year / 52)
    trend = np.arange(n) / n

    # Pivot per-channel spend
    spend_pivot = (
        media_df
        .assign(week_start=lambda d: pd.to_datetime(d["week_start"]))
        .pivot_table(index="week_start", columns="channel", values="spend", aggfunc="sum")
        .reindex(weeks, fill_value=0.0)
    )

    # Compute media contributions using adstock
    media_total = np.zeros(n)
    for ch, coef in CHANNEL_TRUE_COEF.items():
        if ch in spend_pivot.columns:
            adstocked = _adstock(spend_pivot[ch].values, MMM_ADSTOCK_DECAY)
            media_total += coef * adstocked

    # Scale media so it contributes ~30 % of desired mean revenue
    target_mean = 500_000          # target ~$500k/week mean
    media_mean  = media_total.mean()
    media_scale = (0.30 * target_mean) / media_mean
    media_total_scaled = media_total * media_scale

    # Calendar + trend coefficients — chosen so the seasonal swing is ±15 %
    # and trend adds +10 % over the 2-year window.
    intercept = target_mean * 0.60   # base
    A = target_mean * 0.10           # sin amplitude
    B = target_mean * 0.05           # cos amplitude
    C = target_mean * 0.10           # trend lift over full period

    # White noise: ±3 % of target mean
    noise = rng.normal(0, 0.03 * target_mean, n)

    weekly_sales = intercept + A * sin_w + B * cos_w + C * trend \
                   + media_total_scaled + noise

    return weekly_sales.clip(min=50_000)


def run():
    OUTPUT_DIR.mkdir(exist_ok=True)

    start_date = settings.synthetic_start_date
    end_date   = settings.synthetic_end_date
    seed       = settings.synthetic_seed

    print(f"Generating synthetic data: {start_date} → {end_date}  (seed={seed})\n")
    summary = {}

    # ── 1. Media spend ────────────────────────────────────────────────────────
    t0 = time.time()
    print("  [media_spend]  Weekly multi-channel media spend and performance...")
    media_df = media_spend.generate(start_date=start_date, end_date=end_date, seed=seed)
    path = OUTPUT_DIR / "media_spend.parquet"
    media_df.to_parquet(path, index=False)
    elapsed = time.time() - t0
    summary["media_spend"] = {"rows": len(media_df), "columns": len(media_df.columns), "path": str(path)}
    print(f"    -> {len(media_df):,} rows × {len(media_df.columns)} cols  saved to {path}  ({elapsed:.1f}s)")

    # ── 2. Offline sales (MMM-compatible weekly totals) ───────────────────────
    t0 = time.time()
    print("  [offline_sales]  Weekly offline POS data (MMM-causal weekly totals)...")

    # 2a. Generate detailed regional/format/category breakdown (structural scaffold)
    offline_raw = offline_sales.generate(start_date=start_date, end_date=end_date, seed=seed)
    offline_raw["week_start_dt"] = pd.to_datetime(offline_raw["week_start"])

    # 2b. Build true weekly sales using the MMM generative model
    weeks_idx = pd.date_range(start_date, end_date, freq="W-MON")
    true_weekly = _build_true_weekly_sales(media_df, weeks_idx, seed)

    # 2c. Distribute true_weekly proportionally across all rows for each week
    raw_weekly = offline_raw.groupby("week_start_dt")["total_revenue"].transform("sum")
    scale_factor = (
        offline_raw["week_start_dt"]
        .map(dict(zip(weeks_idx, true_weekly)))
        / raw_weekly.clip(lower=1)
    )
    offline_raw["total_revenue"] = (offline_raw["total_revenue"] * scale_factor).round(2)
    offline_raw["revenue_per_store"] = (
        offline_raw["total_revenue"] / offline_raw["active_stores"].clip(lower=1)
    ).round(2)

    offline_final = offline_raw.drop(columns=["week_start_dt"])
    path = OUTPUT_DIR / "offline_sales.parquet"
    offline_final.to_parquet(path, index=False)
    elapsed = time.time() - t0
    summary["offline_sales"] = {"rows": len(offline_final), "columns": len(offline_final.columns), "path": str(path)}
    print(f"    -> {len(offline_final):,} rows × {len(offline_final.columns)} cols  saved to {path}  ({elapsed:.1f}s)")

    # Quick sanity check
    weekly_check = offline_final.groupby("week_start")["total_revenue"].sum()
    print(f"    Weekly revenue range: ${weekly_check.min():,.0f} – ${weekly_check.max():,.0f}")

    # ── 3. Online sales ───────────────────────────────────────────────────────
    t0 = time.time()
    print("  [online_sales]  Daily online sales by channel and category...")
    online_df = online_sales.generate(start_date=start_date, end_date=end_date, seed=seed)
    path = OUTPUT_DIR / "online_sales.parquet"
    online_df.to_parquet(path, index=False)
    elapsed = time.time() - t0
    summary["online_sales"] = {"rows": len(online_df), "columns": len(online_df.columns), "path": str(path)}
    print(f"    -> {len(online_df):,} rows × {len(online_df.columns)} cols  saved to {path}  ({elapsed:.1f}s)")

    # ── 4. CRM funnel ─────────────────────────────────────────────────────────
    t0 = time.time()
    print("  [crm_funnel]  CRM funnel contacts from lead through close...")
    crm_df = crm_funnel.generate(start_date=start_date, end_date=end_date, seed=seed)
    path = OUTPUT_DIR / "crm_funnel.parquet"
    crm_df.to_parquet(path, index=False)
    elapsed = time.time() - t0
    summary["crm_funnel"] = {"rows": len(crm_df), "columns": len(crm_df.columns), "path": str(path)}
    print(f"    -> {len(crm_df):,} rows × {len(crm_df.columns)} cols  saved to {path}  ({elapsed:.1f}s)")

    # ── 5. Account revenue ────────────────────────────────────────────────────────
    t0 = time.time()
    print("  [account_revenue]  Monthly account revenue time series...")
    # Load CRM funnel to get closed-won accounts
    crm_df = pd.read_parquet(OUTPUT_DIR / "crm_funnel.parquet")
    acct_df, acct_summary = account_revenue.generate(crm_df, seed=seed)
    acct_df.to_parquet(OUTPUT_DIR / "account_revenue.parquet", index=False)
    acct_summary.to_parquet(OUTPUT_DIR / "account_summary.parquet", index=False)
    elapsed = time.time() - t0
    summary["account_revenue"] = {
        "rows": len(acct_df),
        "columns": len(acct_df.columns),
        "path": str(OUTPUT_DIR / "account_revenue.parquet"),
    }
    print(f"    -> {len(acct_df):,} monthly rows, {len(acct_summary):,} accounts  ({elapsed:.1f}s)")

    print("\nDone. Summary:")
    for name, info in summary.items():
        print(f"  {name:<20} {info['rows']:>8,} rows  →  {info['path']}")


if __name__ == "__main__":
    run()
