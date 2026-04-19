"""Tests for synthetic data generators."""
import pandas as pd
import pytest

START = "2023-01-01"
END   = "2023-06-30"


def test_online_sales_shape_and_columns():
    from synthetic_data.online_sales import generate
    df = generate(START, END, seed=0)
    assert len(df) > 0
    assert {"date", "channel", "category", "revenue", "orders"}.issubset(df.columns)


def test_online_sales_no_negative_revenue():
    from synthetic_data.online_sales import generate
    df = generate(START, END, seed=0)
    assert (df["revenue"] >= 0).all()


def test_online_sales_promo_flag_binary():
    from synthetic_data.online_sales import generate
    df = generate(START, END, seed=0)
    assert df["promo_flag"].isin([0, 1]).all()


def test_offline_sales_shape_and_columns():
    from synthetic_data.offline_sales import generate
    df = generate(START, END, seed=0)
    assert len(df) > 0
    assert {"week_start", "region", "store_format", "category", "total_revenue"}.issubset(df.columns)


def test_offline_sales_positive_revenue():
    from synthetic_data.offline_sales import generate
    df = generate(START, END, seed=0)
    assert (df["total_revenue"] > 0).all()


def test_crm_funnel_shape_and_columns():
    from synthetic_data.crm_funnel import generate
    df = generate(START, END, seed=0)
    assert len(df) > 0
    required = {"contact_id", "lead_source", "outcome", "reached_mql", "reached_sql"}
    assert required.issubset(df.columns)


def test_crm_funnel_monotonic_conversions():
    """SQL reached count must be <= MQL count."""
    from synthetic_data.crm_funnel import generate
    df = generate(START, END, seed=0)
    assert df["reached_sql"].sum() <= df["reached_mql"].sum()
    assert df["reached_opp"].sum() <= df["reached_sql"].sum()
    assert df["reached_close"].sum() <= df["reached_opp"].sum()


def test_media_spend_shape_and_channels():
    from synthetic_data.media_spend import generate
    df = generate(START, END, seed=0)
    assert len(df) > 0
    assert "channel" in df.columns
    assert "spend" in df.columns
    assert (df["spend"] > 0).all()


def test_media_spend_contribution_pct_sums_to_one():
    from synthetic_data.media_spend import generate
    df = generate(START, END, seed=0)
    totals = df.groupby("week_start")["media_contribution_pct"].sum()
    assert (totals.round(2) == 1.0).all(), "Contribution pcts should sum to 1 per week"


def test_seed_reproducibility():
    from synthetic_data.online_sales import generate
    df1 = generate(START, END, seed=99)
    df2 = generate(START, END, seed=99)
    pd.testing.assert_frame_equal(df1, df2)
