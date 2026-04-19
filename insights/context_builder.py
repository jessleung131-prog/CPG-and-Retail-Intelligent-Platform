"""
Builds a structured context payload from dashboard data to feed into Claude.

Aggregates KPIs, channel contributions, funnel metrics, anomalies,
and forecast results into a compact JSON-serialisable dict.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from api.data_loader import (
    load_online_sales,
    load_offline_sales,
    load_media_spend,
    load_crm_funnel,
)


def build_context(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Collect all dashboard metrics into one structured context dict.
    Used as the data payload for Claude insight generation.
    """
    from api.filters import FilterParams, apply_filters

    params = FilterParams(start_date=start_date, end_date=end_date)

    # ── Online Sales ──────────────────────────────────────────────────────────
    online = apply_filters(load_online_sales(), "date", params)
    online_rev = float(online["revenue"].sum())
    online_by_channel = (
        online.groupby("channel")["revenue"].sum()
        .sort_values(ascending=False)
        .round(0)
        .to_dict()
    )
    online_by_category = (
        online.groupby("category")["revenue"].sum()
        .sort_values(ascending=False)
        .round(0)
        .to_dict()
    )
    # Month-over-month trend (last 2 months)
    online["month"] = pd.to_datetime(online["date"]).dt.to_period("M")
    monthly = online.groupby("month")["revenue"].sum()
    mom_change = None
    if len(monthly) >= 2:
        prev, curr = float(monthly.iloc[-2]), float(monthly.iloc[-1])
        mom_change = round((curr - prev) / max(prev, 1) * 100, 2)

    # ── Offline Sales ─────────────────────────────────────────────────────────
    offline = apply_filters(load_offline_sales(), "week_start", params)
    offline_rev = float(offline["total_revenue"].sum())
    offline_by_region = (
        offline.groupby("region")["total_revenue"].sum()
        .sort_values(ascending=False)
        .round(0)
        .to_dict()
    )

    # ── Media Spend ───────────────────────────────────────────────────────────
    media = apply_filters(load_media_spend(), "week_start", params)
    total_spend = float(media["spend"].sum())
    roas_by_channel = (
        media.groupby("channel")["roas"].mean()
        .sort_values(ascending=False)
        .round(3)
        .to_dict()
    )
    spend_by_channel = (
        media.groupby("channel")["spend"].sum()
        .sort_values(ascending=False)
        .round(0)
        .to_dict()
    )
    blended_roas = round(
        float(media["incremental_revenue"].sum()) / max(total_spend, 1), 2
    )

    # ── CRM Funnel ────────────────────────────────────────────────────────────
    crm = apply_filters(load_crm_funnel(), "lead_date", params)
    total_leads = len(crm)
    closed_won = crm[crm["outcome"] == "Closed Won"]
    win_rate = round(len(closed_won) / max(total_leads, 1) * 100, 2)
    pipeline_value = float(closed_won["deal_value"].sum())
    avg_deal = float(closed_won["deal_value"].mean() or 0)

    # Top and bottom lead sources by win rate
    source_perf = (
        crm.groupby("lead_source")
        .agg(leads=("contact_id", "count"), won=("reached_close", "sum"))
        .assign(win_rate=lambda d: (d["won"] / d["leads"].clip(lower=1) * 100).round(2))
        .sort_values("win_rate", ascending=False)
    )
    top_source = source_perf.index[0] if len(source_perf) > 0 else None
    bottom_source = source_perf.index[-1] if len(source_perf) > 0 else None

    return {
        "period": {
            "start": start_date or str(pd.to_datetime(online["date"]).min().date()),
            "end":   end_date   or str(pd.to_datetime(online["date"]).max().date()),
        },
        "revenue": {
            "online_total": round(online_rev, 0),
            "offline_total": round(offline_rev, 0),
            "combined_total": round(online_rev + offline_rev, 0),
            "online_share_pct": round(online_rev / max(online_rev + offline_rev, 1) * 100, 1),
            "mom_online_change_pct": mom_change,
            "by_channel": online_by_channel,
            "by_category": online_by_category,
            "offline_by_region": offline_by_region,
        },
        "media": {
            "total_spend": round(total_spend, 0),
            "blended_roas": blended_roas,
            "roas_by_channel": roas_by_channel,
            "spend_by_channel": spend_by_channel,
        },
        "crm": {
            "total_leads": total_leads,
            "win_rate_pct": win_rate,
            "pipeline_closed_won": round(pipeline_value, 0),
            "avg_deal_value": round(avg_deal, 0),
            "top_lead_source": top_source,
            "bottom_lead_source": bottom_source,
        },
    }
