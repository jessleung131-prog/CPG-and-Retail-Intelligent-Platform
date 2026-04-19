"""
/kpis — top-level KPI summary across all data streams.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
import pandas as pd

from api.data_loader import load_online_sales, load_offline_sales, load_media_spend, load_crm_funnel
from api.filters import FilterParams, apply_filters, reliability_warning

router = APIRouter(prefix="/kpis", tags=["KPIs"])


@router.get("/summary")
def kpi_summary(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
):
    """
    Return top-level KPIs: total revenue, online vs offline split,
    total media spend, ROAS, CRM win rate and pipeline value.
    """
    params = FilterParams(start_date=start_date, end_date=end_date)
    warnings = []

    # Online revenue
    online = apply_filters(load_online_sales(), "date", params)
    w = reliability_warning(online, "online sales")
    if w:
        warnings.append(w)
    online_rev = float(online["revenue"].sum())
    online_orders = int(online["orders"].sum())

    # Offline revenue
    offline = apply_filters(load_offline_sales(), "week_start", params)
    offline_rev = float(offline["total_revenue"].sum())

    # Media spend + ROAS
    media = apply_filters(load_media_spend(), "week_start", params)
    total_spend = float(media["spend"].sum())
    total_incr_rev = float(media["incremental_revenue"].sum())
    blended_roas = round(total_incr_rev / max(total_spend, 1), 2)

    # CRM
    crm = apply_filters(load_crm_funnel(), "lead_date", params)
    total_leads = int(len(crm))
    closed_won = crm[crm["outcome"] == "Closed Won"]
    pipeline_value = float(closed_won["deal_value"].sum())
    win_rate = round(len(closed_won) / max(total_leads, 1) * 100, 2)

    total_revenue = online_rev + offline_rev

    return {
        "total_revenue": round(total_revenue, 2),
        "online_revenue": round(online_rev, 2),
        "offline_revenue": round(offline_rev, 2),
        "online_share_pct": round(online_rev / max(total_revenue, 1) * 100, 2),
        "total_orders_online": online_orders,
        "total_media_spend": round(total_spend, 2),
        "blended_roas": blended_roas,
        "total_leads": total_leads,
        "pipeline_closed_won": round(pipeline_value, 2),
        "win_rate_pct": win_rate,
        "warnings": warnings,
    }


@router.get("/trend")
def kpi_trend(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    granularity: str = Query("weekly", description="daily | weekly | monthly"),
):
    """
    Return revenue trend at the requested granularity.
    """
    params = FilterParams(start_date=start_date, end_date=end_date)
    warnings = []

    online = apply_filters(load_online_sales(), "date", params)
    freq_map = {"daily": "D", "weekly": "W-MON", "monthly": "MS"}
    freq = freq_map.get(granularity, "W-MON")

    online_trend = (
        online.set_index("date")
        .resample(freq)["revenue"]
        .sum()
        .reset_index()
        .rename(columns={"date": "period", "revenue": "online_revenue"})
    )

    offline = apply_filters(load_offline_sales(), "week_start", params)
    offline_trend = (
        offline.set_index("week_start")
        .resample(freq)["total_revenue"]
        .sum()
        .reset_index()
        .rename(columns={"week_start": "period", "total_revenue": "offline_revenue"})
    )

    trend = online_trend.merge(offline_trend, on="period", how="outer").fillna(0)
    trend["total_revenue"] = trend["online_revenue"] + trend["offline_revenue"]
    trend["period"] = trend["period"].dt.strftime("%Y-%m-%d")

    w = reliability_warning(trend, "trend")
    if w:
        warnings.append(w)

    return {
        "granularity": granularity,
        "data": trend.to_dict(orient="records"),
        "warnings": warnings,
    }
