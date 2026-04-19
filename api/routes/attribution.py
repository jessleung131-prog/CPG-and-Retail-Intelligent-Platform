"""
/attribution — MMM channel contribution and incremental ROI.
"""
from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd

from api.data_loader import load_media_spend, load_offline_sales
from api.filters import FilterParams, apply_filters, reliability_warning

router = APIRouter(prefix="/attribution", tags=["Attribution"])


@router.get("/channel-contribution")
def channel_contribution(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
):
    """
    Run MMM and return channel contribution %, incremental revenue, and ROI.
    """
    from models.mmm import run_mmm

    params = FilterParams(start_date=start_date, end_date=end_date)
    warnings = []

    media_df = apply_filters(load_media_spend(), "week_start", params)
    sales_df = apply_filters(load_offline_sales(), "week_start", params)
    sales_agg = sales_df.groupby("week_start", as_index=False)["total_revenue"].sum()

    w = reliability_warning(media_df, "media spend")
    if w:
        warnings.append(w)

    result = run_mmm(media_df, sales_agg)

    if result.confidence_warning:
        warnings.append(result.confidence_warning)

    contrib = result.channel_contributions.to_dict(orient="records")

    decomp = result.decomposition.copy()
    decomp["week_start"] = pd.to_datetime(decomp["week_start"]).dt.strftime("%Y-%m-%d")

    return {
        "metrics": result.metrics,
        "channel_contributions": contrib,
        "decomposition": decomp.to_dict(orient="records"),
        "warnings": warnings,
    }


@router.get("/spend-efficiency")
def spend_efficiency(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
):
    """
    Return per-channel spend efficiency: CPM, CTR, CVR, CPA, ROAS.
    """
    params = FilterParams(start_date=start_date, end_date=end_date)
    warnings = []

    media = apply_filters(load_media_spend(), "week_start", params)
    w = reliability_warning(media, "media spend")
    if w:
        warnings.append(w)

    summary = (
        media.groupby("channel")
        .agg(
            total_spend=("spend", "sum"),
            total_impressions=("impressions", "sum"),
            total_clicks=("clicks", "sum"),
            total_conversions=("conversions", "sum"),
            avg_roas=("roas", "mean"),
            avg_cpm=("cpm", "mean"),
            avg_ctr=("ctr", "mean"),
            avg_cpa=("cpa", "mean"),
        )
        .reset_index()
        .round(3)
        .to_dict(orient="records")
    )

    return {"data": summary, "warnings": warnings}
