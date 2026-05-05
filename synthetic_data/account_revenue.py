"""
Account revenue time series generator.

Generates monthly revenue trajectories for all closed-won CRM accounts,
plus an account-level summary table with churn/growth features.

Outputs:
    data/account_revenue.parquet  — one row per account per active month
    data/account_summary.parquet  — one row per account (feature table)
"""
import numpy as np
import pandas as pd
from scipy import stats

DATASET_END = pd.Timestamp("2024-12-31")
DATASET_START_MONTH = pd.Timestamp("2023-01-01")

INDUSTRY_PHASES = {
    "Grocery Retail":  0.0,
    "Drug Store":      1.0,
    "Foodservice":     2.0,
    "Specialty Retail": 3.5,
    "Mass Merchant":   5.0,
}


def _deal_size_band(deal_value: float) -> str:
    if deal_value < 20_000:
        return "Small"
    elif deal_value <= 60_000:
        return "Mid"
    else:
        return "Large"


def _assign_churn_month(rng) -> int | None:
    """
    Returns the churn month index (1-based) or None (survives full 24 months).

    Probabilities:
      15% churn months 1-6
      25% churn months 7-18
      10% churn months 19-24
      50% survive all 24 months
    """
    roll = rng.random()
    if roll < 0.15:
        return int(rng.integers(1, 7))        # 1..6
    elif roll < 0.40:
        return int(rng.integers(7, 19))       # 7..18
    elif roll < 0.50:
        return int(rng.integers(19, 25))      # 19..24
    else:
        return None   # survives


def generate(crm_df: pd.DataFrame, seed: int = 42):
    """
    Generate monthly account revenue for all closed-won accounts.

    Parameters
    ----------
    crm_df : DataFrame
        Full CRM funnel data (must include outcome, contact_id, industry,
        deal_value, close_date, lead_source columns).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    (monthly_df, summary_df) tuple of DataFrames.
    """
    rng = np.random.default_rng(seed)

    # Filter to closed-won only
    won = crm_df[crm_df["outcome"] == "Closed Won"].copy()
    won["close_date"] = pd.to_datetime(won["close_date"])
    won = won.dropna(subset=["deal_value", "close_date"])

    # Assign deal_size_band
    won["deal_size_band"] = won["deal_value"].apply(_deal_size_band)

    monthly_rows = []

    for _, acct in won.iterrows():
        acct_id = acct["contact_id"]
        industry = acct["industry"]
        lead_source = acct["lead_source"]
        deal_value = float(acct["deal_value"])
        close_date = acct["close_date"]
        band = acct["deal_size_band"]

        # Base monthly revenue ~ 8% of deal_value
        base_rev = deal_value * 0.08

        # Per-account growth rate ~ N(0.008, 0.015)
        growth_rate = float(rng.normal(0.008, 0.015))

        # Industry seasonality phase
        phase = INDUSTRY_PHASES.get(industry, 0.0)

        # Churn month (None = survives all 24 months)
        churn_month = _assign_churn_month(rng)

        # Generate month sequence: month after close_date up to DATASET_END
        # Cap at 24 months max
        first_month = (close_date + pd.offsets.MonthBegin(1)).normalize()
        months = pd.date_range(start=first_month, end=DATASET_END, freq="MS")
        months = months[:24]  # cap at 24 months

        for m_idx, month in enumerate(months):
            m = m_idx + 1  # 1-based month number

            if churn_month is not None and m >= churn_month:
                rev = 0.0
            else:
                # Growth component
                growth_mult = (1 + growth_rate) ** m

                # Seasonality: sin wave, different phase per industry
                month_of_year = month.month
                seasonal = 1.0 + 0.12 * np.sin(
                    2 * np.pi * month_of_year / 12 + phase
                )

                # Multiplicative noise
                noise = float(rng.normal(1.0, 0.08))

                rev = base_rev * growth_mult * seasonal * noise
                rev = max(0.0, rev)

            monthly_rows.append({
                "account_id": acct_id,
                "industry": industry,
                "lead_source": lead_source,
                "deal_size_band": band,
                "close_date": close_date,
                "month": month,
                "monthly_revenue": round(rev, 2),
                "months_since_close": m,
            })

    monthly_df = pd.DataFrame(monthly_rows)

    # ── Account-level summary ────────────────────────────────────────────────
    last_3m_start   = pd.Timestamp("2024-10-01")
    prev_3m_start   = pd.Timestamp("2024-07-01")
    last_6m_start   = pd.Timestamp("2024-07-01")

    summary_rows = []

    for acct_id, grp in monthly_df.groupby("account_id"):
        grp = grp.sort_values("month")

        row0 = grp.iloc[0]
        industry     = row0["industry"]
        lead_source  = row0["lead_source"]
        band         = row0["deal_size_band"]
        close_date   = row0["close_date"]

        deal_value = float(won.loc[
            won["contact_id"] == acct_id, "deal_value"
        ].iloc[0])

        active = grp[grp["monthly_revenue"] > 0]
        months_active = len(active)
        total_revenue = float(grp["monthly_revenue"].sum())
        avg_monthly_revenue = float(active["monthly_revenue"].mean()) if months_active > 0 else 0.0

        # Last 3m and prev 3m averages (Oct–Dec 2024, Jul–Sep 2024)
        last_3m = grp[grp["month"] >= last_3m_start]["monthly_revenue"]
        prev_3m = grp[
            (grp["month"] >= prev_3m_start) & (grp["month"] < last_3m_start)
        ]["monthly_revenue"]

        last_3m_avg = float(last_3m.mean()) if len(last_3m) > 0 else 0.0
        prev_3m_avg = float(prev_3m.mean()) if len(prev_3m) > 0 else 0.0

        # Revenue trend slope over last 6 months
        last_6m = grp[grp["month"] >= last_6m_start][["month", "monthly_revenue"]]
        if len(last_6m) >= 2:
            x = np.arange(len(last_6m), dtype=float)
            slope, *_ = stats.linregress(x, last_6m["monthly_revenue"].values)
            revenue_trend_slope = float(slope)
        else:
            revenue_trend_slope = 0.0

        # MoM growth (last_3m vs prev_3m)
        if prev_3m_avg > 0:
            mom_raw = (last_3m_avg - prev_3m_avg) / prev_3m_avg
            mom_growth_3m = float(np.clip(mom_raw, -0.5, 1.0))
        else:
            mom_growth_3m = 0.0

        # Months since last order (from 2024-12-31)
        active_months = grp[grp["monthly_revenue"] > 0]["month"]
        if len(active_months) > 0:
            last_order = active_months.max()
            months_since_last_order = int(
                round((DATASET_END - last_order).days / 30.44)
            )
        else:
            months_since_last_order = int(
                round((DATASET_END - grp["month"].min()).days / 30.44)
            )

        # Revenue volatility
        if months_active >= 2:
            revenue_volatility = float(active["monthly_revenue"].std())
        else:
            revenue_volatility = 0.0

        # is_churned: 1 if all last 3 months are zero
        last_3_revs = last_3m.values if len(last_3m) == 3 else np.array([])
        is_churned = int(len(last_3_revs) == 3 and all(v == 0.0 for v in last_3_revs))

        # months_since_close — from end of dataset
        months_since_close = int(
            round((DATASET_END - pd.Timestamp(close_date)).days / 30.44)
        )

        summary_rows.append({
            "account_id": acct_id,
            "industry": industry,
            "lead_source": lead_source,
            "deal_size_band": band,
            "close_date": close_date,
            "deal_value": deal_value,
            "months_active": months_active,
            "total_revenue": round(total_revenue, 2),
            "avg_monthly_revenue": round(avg_monthly_revenue, 2),
            "last_3m_avg": round(last_3m_avg, 2),
            "prev_3m_avg": round(prev_3m_avg, 2),
            "revenue_trend_slope": round(revenue_trend_slope, 4),
            "mom_growth_3m": round(mom_growth_3m, 4),
            "months_since_last_order": months_since_last_order,
            "revenue_volatility": round(revenue_volatility, 2),
            "is_churned": is_churned,
            "months_since_close": months_since_close,
        })

    summary_df = pd.DataFrame(summary_rows)

    return monthly_df, summary_df


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import settings

    crm_path = Path(__file__).resolve().parent.parent / "data" / "crm_funnel.parquet"
    crm_df = pd.read_parquet(crm_path)

    print(f"Loaded {len(crm_df):,} CRM rows. Closed Won: "
          f"{(crm_df['outcome']=='Closed Won').sum():,}")

    monthly_df, summary_df = generate(crm_df, seed=42)

    print(f"\nMonthly rows : {len(monthly_df):,}")
    print(f"Accounts     : {len(summary_df):,}")
    print(f"\nMonthly revenue stats:")
    print(monthly_df["monthly_revenue"].describe())
    print(f"\nSummary head:")
    print(summary_df.head())
    print(f"\nChurned accounts: {summary_df['is_churned'].sum()}")
