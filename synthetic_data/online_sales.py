"""
Online sales synthetic data generator.

Produces daily records per channel (DTC, Amazon, Walmart.com) with:
  - Baseline revenue driven by a long-term growth trend
  - Yearly + weekly seasonality
  - Promotional lift events (flash sales, holiday campaigns)
  - Realistic noise
"""
import numpy as np
import pandas as pd
from datetime import date


# Channels and their relative size weights
CHANNELS = {
    "DTC": 0.40,
    "Amazon": 0.35,
    "Walmart.com": 0.25,
}

# Product categories
CATEGORIES = ["Beverages", "Snacks", "Personal Care", "Household"]

# Holiday / promotional windows (month-day start, month-day end, lift multiplier)
PROMO_WINDOWS = [
    # (start_md, end_md, lift)
    ("02-10", "02-14", 1.20),   # Valentine's Day
    ("05-25", "05-27", 1.25),   # Memorial Day
    ("07-04", "07-06", 1.15),   # Independence Day
    ("11-25", "11-30", 1.55),   # Black Friday / Cyber Monday
    ("12-20", "12-26", 1.45),   # Christmas week
    ("12-30", "12-31", 1.10),   # New Year's Eve
]


def _promo_multiplier(date_series: pd.Series) -> pd.Series:
    """Return a daily promo lift multiplier (1.0 = no promo)."""
    multiplier = pd.Series(1.0, index=date_series.index)
    for start_md, end_md, lift in PROMO_WINDOWS:
        month_s, day_s = map(int, start_md.split("-"))
        month_e, day_e = map(int, end_md.split("-"))
        mask = (
            (date_series.dt.month == month_s) & (date_series.dt.day >= day_s)
        ) | (
            (date_series.dt.month == month_e) & (date_series.dt.day <= day_e)
        )
        multiplier = multiplier.where(~mask, multiplier * lift)
    return multiplier


def generate(
    start_date: str,
    end_date: str,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate daily online sales data.

    Returns a DataFrame with columns:
        date, channel, category, orders, revenue, avg_order_value,
        units_sold, returns, return_rate, promo_flag
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start_date, end_date, freq="D")
    n = len(dates)

    # Annual seasonality (peaks around summer + Q4)
    day_of_year = pd.Series(dates).dt.dayofyear.values
    seasonal = 1.0 + 0.25 * np.sin(2 * np.pi * (day_of_year - 60) / 365)

    # Long-term growth trend (≈15 % YoY)
    trend = 1.0 + 0.15 * np.arange(n) / 365

    # Day-of-week effect (Mon index=0 → higher weekday for DTC, weekend for Amazon)
    dow = pd.Series(dates).dt.dayofweek.values  # 0=Mon … 6=Sun
    dow_effect = 1.0 + 0.08 * np.sin(np.pi * dow / 3)

    date_series = pd.Series(dates)
    promo = _promo_multiplier(date_series).values

    records = []
    for channel, weight in CHANNELS.items():
        for cat in CATEGORIES:
            # Base daily orders for this channel + category
            base_orders = weight * 0.25 * 800  # 800 total daily orders split by channel/cat

            orders = (
                base_orders
                * seasonal
                * trend
                * dow_effect
                * promo
                * (1.0 + rng.normal(0, 0.05, n))
            ).clip(min=1).astype(int)

            # Average order value varies by channel
            aov_base = {"DTC": 48, "Amazon": 35, "Walmart.com": 28}[channel]
            aov = aov_base * (1 + rng.normal(0, 0.04, n))

            revenue = (orders * aov).round(2)
            units = (orders * rng.uniform(1.5, 2.5, n)).astype(int)
            return_rate = rng.beta(2, 40, n).round(4)  # ~5 % mean return rate
            returns = (orders * return_rate).astype(int)

            df_channel = pd.DataFrame(
                {
                    "date": dates,
                    "channel": channel,
                    "category": cat,
                    "orders": orders,
                    "revenue": revenue,
                    "avg_order_value": aov.round(2),
                    "units_sold": units,
                    "returns": returns,
                    "return_rate": return_rate,
                    "promo_flag": (promo > 1.0).astype(int),
                }
            )
            records.append(df_channel)

    df = pd.concat(records, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values(["date", "channel", "category"]).reset_index(drop=True)


if __name__ == "__main__":
    df = generate("2023-01-01", "2024-12-31")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Date range: {df['date'].min()} → {df['date'].max()}")
    print(f"Revenue total: ${df['revenue'].sum():,.0f}")
