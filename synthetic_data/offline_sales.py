"""
Offline (brick-and-mortar) sales synthetic data generator.

Produces weekly store-level POS data across regions with:
  - Regional store counts growing over time (distribution expansion)
  - Seasonal patterns and promotional lifts
  - Product category mix
  - Realistic per-store revenue and units
"""
import numpy as np
import pandas as pd


REGIONS = {
    "Northeast": {"initial_stores": 120, "growth_rate": 0.05},
    "Southeast": {"initial_stores": 95,  "growth_rate": 0.08},
    "Midwest":   {"initial_stores": 80,  "growth_rate": 0.06},
    "Southwest": {"initial_stores": 60,  "growth_rate": 0.10},
    "West":      {"initial_stores": 75,  "growth_rate": 0.07},
}

CATEGORIES = ["Beverages", "Snacks", "Personal Care", "Household"]

STORE_FORMATS = ["Supermarket", "Club Store", "Drug Store", "Mass Merchant"]

# Promotional periods: (month start, month end, lift)
PROMO_PERIODS = [
    (2, 2, 1.12),   # Valentine's Day
    (5, 5, 1.18),   # Memorial Day
    (7, 7, 1.10),   # 4th of July
    (11, 11, 1.40), # Thanksgiving / Black Friday
    (12, 12, 1.35), # Christmas
]


def _weekly_promo(week_dates: pd.Series) -> np.ndarray:
    multiplier = np.ones(len(week_dates))
    months = week_dates.dt.month.values
    for m_start, m_end, lift in PROMO_PERIODS:
        mask = (months >= m_start) & (months <= m_end)
        multiplier[mask] *= lift
    return multiplier


def generate(
    start_date: str,
    end_date: str,
    seed: int = 42,
    media_lift: "pd.Series | None" = None,
) -> pd.DataFrame:
    """
    Generate weekly offline sales data.

    Args:
        start_date:  ISO date string for first week.
        end_date:    ISO date string for last week.
        seed:        Random seed for reproducibility.
        media_lift:  Optional Series indexed by week_start (date objects) with
                     weekly media incremental revenue values.  When provided,
                     weeks with higher media investment receive a proportional
                     revenue lift (up to ~30 %), creating a causal link that
                     the MMM can recover.

    Returns a DataFrame with columns:
        week_start, region, store_format, category,
        active_stores, total_revenue, revenue_per_store,
        units_sold, avg_selling_price, promo_flag,
        distribution_pct
    """
    rng = np.random.default_rng(seed)
    weeks = pd.date_range(start_date, end_date, freq="W-MON")
    n_weeks = len(weeks)

    # Fraction through the date range (0→1) for growth calculations
    time_frac = np.linspace(0, 1, n_weeks)
    seasonal = 1.0 + 0.20 * np.sin(2 * np.pi * (weeks.dayofyear.to_numpy() - 90) / 365)
    promo = _weekly_promo(pd.Series(weeks))

    # Build a weekly media-driven multiplier (1.0 = no lift, up to ~1.30)
    if media_lift is not None:
        lift_vals = np.array([
            float(media_lift.get(w.date(), 0.0)) for w in weeks
        ])
        lift_min, lift_max = lift_vals.min(), lift_vals.max()
        if lift_max > lift_min:
            lift_norm = (lift_vals - lift_min) / (lift_max - lift_min)  # 0→1
        else:
            lift_norm = np.zeros(n_weeks)
        media_multiplier = 1.0 + 0.45 * lift_norm   # up to 45 % additive lift
    else:
        media_multiplier = np.ones(n_weeks)

    records = []
    for region, cfg in REGIONS.items():
        # Store count grows over time
        stores = (
            cfg["initial_stores"] * (1 + cfg["growth_rate"]) ** (time_frac * 2)
        ).astype(int)

        for fmt in STORE_FORMATS:
            fmt_weight = {"Supermarket": 0.40, "Club Store": 0.20,
                          "Drug Store": 0.25, "Mass Merchant": 0.15}[fmt]
            for cat in CATEGORIES:
                cat_weight = {"Beverages": 0.30, "Snacks": 0.28,
                              "Personal Care": 0.22, "Household": 0.20}[cat]

                base_rev_per_store = 2_800 * fmt_weight * cat_weight

                noise = 1.0 + rng.normal(0, 0.06, n_weeks)
                trend = 1.0 + 0.12 * time_frac  # 12 % growth over 2 years

                rev_per_store = (
                    base_rev_per_store * seasonal * trend * promo * noise * media_multiplier
                ).clip(min=50)

                total_rev = (rev_per_store * stores * fmt_weight).round(2)

                avg_price = {"Beverages": 5.50, "Snacks": 4.80,
                             "Personal Care": 8.20, "Household": 7.40}[cat]
                avg_price_w_noise = avg_price * (1 + rng.normal(0, 0.02, n_weeks))
                units = (total_rev / avg_price_w_noise).astype(int)

                distribution_pct = (
                    0.60 + 0.25 * time_frac + rng.normal(0, 0.02, n_weeks)
                ).clip(0, 1).round(4)

                records.append(
                    pd.DataFrame(
                        {
                            "week_start": weeks.date,
                            "region": region,
                            "store_format": fmt,
                            "category": cat,
                            "active_stores": stores,
                            "total_revenue": total_rev,
                            "revenue_per_store": rev_per_store.round(2),
                            "units_sold": units,
                            "avg_selling_price": avg_price_w_noise.round(2),
                            "promo_flag": (promo > 1.0).astype(int),
                            "distribution_pct": distribution_pct,
                        }
                    )
                )

    df = pd.concat(records, ignore_index=True)
    return df.sort_values(["week_start", "region", "store_format", "category"]).reset_index(drop=True)


if __name__ == "__main__":
    df = generate("2023-01-01", "2024-12-31")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Week range: {df['week_start'].min()} → {df['week_start'].max()}")
    print(f"Revenue total: ${df['total_revenue'].sum():,.0f}")
