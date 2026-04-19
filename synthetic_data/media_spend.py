"""
Multi-channel media spend and performance synthetic data generator.

Models weekly spend + impression/click/conversion performance across channels
with realistic patterns including:
  - Adstock / carryover effects (spend in prior weeks still drives conversions)
  - Diminishing returns (saturation) at high spend levels
  - Seasonal budget flighting
  - Channel-level efficiency benchmarks (CPM, CTR, ROAS)
"""
import numpy as np
import pandas as pd


# Channel definitions: base weekly spend, efficiency params
CHANNELS = {
    "Paid Search": {
        "base_spend":    18_000,
        "cpm":           8.0,
        "ctr":           0.045,
        "cvr":           0.035,
        "roas_base":     4.2,
        "adstock_decay": 0.30,  # 30% carryover to next week
        "saturation_k":  0.00005,
    },
    "Paid Social": {
        "base_spend":    22_000,
        "cpm":           11.0,
        "ctr":           0.012,
        "cvr":           0.018,
        "roas_base":     2.8,
        "adstock_decay": 0.45,
        "saturation_k":  0.00004,
    },
    "Display": {
        "base_spend":    12_000,
        "cpm":           4.5,
        "ctr":           0.003,
        "cvr":           0.008,
        "roas_base":     1.5,
        "adstock_decay": 0.55,
        "saturation_k":  0.00003,
    },
    "TV / CTV": {
        "base_spend":    45_000,
        "cpm":           25.0,
        "ctr":           0.0,   # Not directly clickable
        "cvr":           0.0,
        "roas_base":     1.8,
        "adstock_decay": 0.70,  # TV has long carryover
        "saturation_k":  0.00001,
    },
    "Email": {
        "base_spend":    3_500,
        "cpm":           0.8,
        "ctr":           0.025,
        "cvr":           0.055,
        "roas_base":     8.5,
        "adstock_decay": 0.10,
        "saturation_k":  0.0001,
    },
    "Influencer": {
        "base_spend":    15_000,
        "cpm":           14.0,
        "ctr":           0.018,
        "cvr":           0.022,
        "roas_base":     2.3,
        "adstock_decay": 0.50,
        "saturation_k":  0.00003,
    },
}


def _adstock(spend_series: np.ndarray, decay: float) -> np.ndarray:
    """Geometric adstock transform."""
    adstocked = np.zeros_like(spend_series, dtype=float)
    for t in range(len(spend_series)):
        adstocked[t] = spend_series[t] + (adstocked[t - 1] * decay if t > 0 else 0)
    return adstocked


def _saturation(adstocked: np.ndarray, k: float) -> np.ndarray:
    """Hill / diminishing-returns saturation: S(x) = x / (1 + k*x)."""
    return adstocked / (1 + k * adstocked)


def generate(
    start_date: str,
    end_date: str,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate weekly media spend and performance data per channel.

    Returns a DataFrame with columns:
        week_start, channel,
        spend, impressions, clicks, conversions,
        cpm, ctr, cvr, cpc, cpa,
        roas, adstocked_spend, saturated_spend,
        incremental_revenue, media_contribution_pct
    """
    rng = np.random.default_rng(seed)
    weeks = pd.date_range(start_date, end_date, freq="W-MON")
    n = len(weeks)

    # Seasonal budget index (higher in Q4 and spring)
    day_of_year = weeks.dayofyear.values
    budget_seasonal = 1.0 + 0.30 * np.sin(2 * np.pi * (day_of_year - 60) / 365)

    # Overall budget growth (10% YoY)
    trend = 1.0 + 0.10 * np.arange(n) / n

    records = []
    for channel, cfg in CHANNELS.items():
        # Weekly spend with seasonal + trend + noise
        spend = (
            cfg["base_spend"]
            * budget_seasonal
            * trend
            * (1 + rng.normal(0, 0.08, n))
        ).clip(min=100)

        adstocked = _adstock(spend, cfg["adstock_decay"])
        saturated = _saturation(adstocked, cfg["saturation_k"])

        # Impressions from spend + CPM
        impressions = ((spend / cfg["cpm"]) * 1000 * (1 + rng.normal(0, 0.05, n))).astype(int)

        # Clicks (0 for TV)
        if cfg["ctr"] > 0:
            clicks = (impressions * cfg["ctr"] * (1 + rng.normal(0, 0.10, n))).clip(min=0).astype(int)
        else:
            clicks = np.zeros(n, dtype=int)

        # Conversions
        if cfg["cvr"] > 0 and cfg["ctr"] > 0:
            conversions = (clicks * cfg["cvr"] * (1 + rng.normal(0, 0.12, n))).clip(min=0).astype(int)
        else:
            conversions = np.zeros(n, dtype=int)

        # ROAS varies with saturation — higher at lower spend
        roas = cfg["roas_base"] * (saturated / (spend + 1e-9)) * (1 + rng.normal(0, 0.08, n))
        roas = roas.clip(min=0.5)

        incremental_revenue = (spend * roas).round(2)

        # Derived metrics
        cpm_actual = ((spend / impressions.clip(min=1)) * 1000).round(3)
        ctr_actual = (clicks / impressions.clip(min=1)).round(5)
        cvr_actual = (conversions / clicks.clip(min=1)).round(5)
        cpc = (spend / clicks.clip(min=1)).round(2)
        cpa = (spend / conversions.clip(min=1)).round(2)

        records.append(
            pd.DataFrame(
                {
                    "week_start": weeks.date,
                    "channel": channel,
                    "spend": spend.round(2),
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "cpm": cpm_actual,
                    "ctr": ctr_actual,
                    "cvr": cvr_actual,
                    "cpc": cpc,
                    "cpa": cpa,
                    "roas": roas.round(3),
                    "adstocked_spend": adstocked.round(2),
                    "saturated_spend": saturated.round(2),
                    "incremental_revenue": incremental_revenue,
                }
            )
        )

    df = pd.concat(records, ignore_index=True)

    # Add channel contribution % per week
    total_rev_by_week = df.groupby("week_start")["incremental_revenue"].transform("sum")
    df["media_contribution_pct"] = (df["incremental_revenue"] / total_rev_by_week.clip(lower=1)).round(4)

    return df.sort_values(["week_start", "channel"]).reset_index(drop=True)


if __name__ == "__main__":
    df = generate("2023-01-01", "2024-12-31")
    print(df.head(12))
    print(f"\nShape: {df.shape}")
    print(f"\nTotal spend by channel:\n{df.groupby('channel')['spend'].sum().sort_values(ascending=False).apply(lambda x: f'${x:,.0f}')}")
    print(f"\nAverage ROAS by channel:\n{df.groupby('channel')['roas'].mean().sort_values(ascending=False).round(2)}")
