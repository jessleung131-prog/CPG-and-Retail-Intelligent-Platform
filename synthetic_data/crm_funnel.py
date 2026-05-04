"""
CRM funnel events synthetic data generator.

Models a B2B2C pipeline from lead acquisition through to closed-won,
with realistic stage conversion rates, time lags between stages,
and pipeline health metrics.

Funnel stages:
    Lead → MQL → SQL → Opportunity → Closed Won / Closed Lost
"""
import numpy as np
import pandas as pd
from datetime import timedelta


# Funnel conversion rates (stage → next stage)
CONVERSION_RATES = {
    "lead_to_mql":    0.30,
    "mql_to_sql":     0.45,
    "sql_to_opp":     0.60,
    "opp_to_closed":  0.35,  # win rate
}

# Median days between stages (with some variance)
STAGE_LAG_DAYS = {
    "lead_to_mql":   (3, 7),    # (mean, std)
    "mql_to_sql":    (7, 5),
    "sql_to_opp":    (14, 10),
    "opp_to_closed": (30, 20),
}

# Lead sources
LEAD_SOURCES = {
    "Paid Search":    0.24,
    "Facebook / Instagram": 0.14,
    "TikTok":         0.06,
    "Organic Search": 0.18,
    "Email":          0.12,
    "Events":         0.14,
    "Referral":       0.12,
}

# Industry verticals
INDUSTRIES = ["Grocery Retail", "Drug Store", "Mass Merchant", "Specialty Retail", "Foodservice"]


def _sample_dates(base_dates: pd.Series, mean_lag: int, std_lag: int, rng) -> pd.Series:
    lags = rng.normal(mean_lag, std_lag, len(base_dates)).clip(min=1).astype(int)
    return base_dates + pd.to_timedelta(lags, unit="D")


def generate(
    start_date: str,
    end_date: str,
    seed: int = 42,
    daily_lead_volume: int = 35,
) -> pd.DataFrame:
    """
    Generate CRM funnel event-level records.

    Each row is one contact progressing through the funnel.
    Returns a DataFrame with columns:
        contact_id, lead_source, industry, lead_date,
        mql_date, sql_date, opportunity_date, close_date,
        outcome, deal_value, days_to_close,
        reached_mql, reached_sql, reached_opp, reached_close
    """
    rng = np.random.default_rng(seed)
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    dates = pd.date_range(start, end, freq="D")
    n_days = len(dates)

    # Weekly seasonality for lead volume (lower on weekends)
    dow_factor = np.where(dates.dayofweek < 5, 1.15, 0.30)
    # Growth trend in lead volume
    trend = 1.0 + 0.20 * np.arange(n_days) / n_days

    volumes = (daily_lead_volume * dow_factor * trend
               * (1 + rng.normal(0, 0.12, n_days))).clip(min=0).astype(int)

    records = []
    contact_id = 1

    for day_idx, (day, vol) in enumerate(zip(dates, volumes)):
        if vol == 0:
            continue

        # Sample lead sources
        sources = rng.choice(
            list(LEAD_SOURCES.keys()),
            size=vol,
            p=list(LEAD_SOURCES.values()),
        )
        industries = rng.choice(INDUSTRIES, size=vol)

        for i in range(vol):
            lead_date = day
            source = sources[i]
            industry = industries[i]

            # Progress through funnel stochastically
            mql_date = sql_date = opp_date = close_date = None
            outcome = "Lead Only"
            deal_value = None

            # Lead → MQL
            if rng.random() < CONVERSION_RATES["lead_to_mql"]:
                lag_mean, lag_std = STAGE_LAG_DAYS["lead_to_mql"]
                lag = max(1, int(rng.normal(lag_mean, lag_std)))
                mql_date = lead_date + timedelta(days=lag)

                # MQL → SQL
                if rng.random() < CONVERSION_RATES["mql_to_sql"]:
                    lag_mean, lag_std = STAGE_LAG_DAYS["mql_to_sql"]
                    lag = max(1, int(rng.normal(lag_mean, lag_std)))
                    sql_date = mql_date + timedelta(days=lag)

                    # SQL → Opportunity
                    if rng.random() < CONVERSION_RATES["sql_to_opp"]:
                        lag_mean, lag_std = STAGE_LAG_DAYS["sql_to_opp"]
                        lag = max(1, int(rng.normal(lag_mean, lag_std)))
                        opp_date = sql_date + timedelta(days=lag)

                        # Opportunity → Closed
                        if rng.random() < CONVERSION_RATES["opp_to_closed"]:
                            lag_mean, lag_std = STAGE_LAG_DAYS["opp_to_closed"]
                            lag = max(1, int(rng.normal(lag_mean, lag_std)))
                            close_date = opp_date + timedelta(days=lag)
                            if pd.Timestamp(close_date) <= end:
                                outcome = "Closed Won"
                                deal_value = round(
                                    rng.lognormal(mean=10.5, sigma=0.8), 2
                                )  # Median ~$36k, right-skewed
                            else:
                                outcome = "In Progress"
                        else:
                            close_date = opp_date + timedelta(
                                days=max(7, int(rng.normal(30, 15)))
                            )
                            outcome = "Closed Lost"
                    else:
                        outcome = "SQL Only"
                else:
                    outcome = "MQL Only"

            records.append(
                {
                    "contact_id": f"C{contact_id:07d}",
                    "lead_source": source,
                    "industry": industry,
                    "lead_date": lead_date.date(),
                    "mql_date": mql_date.date() if mql_date else None,
                    "sql_date": sql_date.date() if sql_date else None,
                    "opportunity_date": opp_date.date() if opp_date else None,
                    "close_date": close_date.date() if close_date else None,
                    "outcome": outcome,
                    "deal_value": deal_value,
                    "days_to_close": (
                        (pd.Timestamp(close_date) - lead_date).days
                        if close_date and outcome == "Closed Won"
                        else None
                    ),
                    "reached_mql": int(mql_date is not None),
                    "reached_sql": int(sql_date is not None),
                    "reached_opp": int(opp_date is not None),
                    "reached_close": int(outcome == "Closed Won"),
                }
            )
            contact_id += 1

    df = pd.DataFrame(records)
    return df.sort_values("lead_date").reset_index(drop=True)


if __name__ == "__main__":
    df = generate("2023-01-01", "2024-12-31")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"\nOutcome distribution:\n{df['outcome'].value_counts()}")
    closed = df[df["outcome"] == "Closed Won"]
    print(f"\nClosed Won: {len(closed):,}  |  Total pipeline: ${closed['deal_value'].sum():,.0f}")
