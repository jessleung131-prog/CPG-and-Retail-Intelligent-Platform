"""
/crm — CRM funnel analytics endpoints.
"""
from fastapi import APIRouter, Query
from typing import Optional

from api.data_loader import load_crm_funnel
from api.filters import FilterParams, apply_filters, reliability_warning

router = APIRouter(prefix="/crm", tags=["CRM"])


@router.get("/funnel")
def funnel_summary(
    start_date:  Optional[str] = Query(None),
    end_date:    Optional[str] = Query(None),
    lead_source: Optional[str] = Query(None),
    industry:    Optional[str] = Query(None),
):
    """
    Return funnel stage conversion rates and volumes.
    """
    params = FilterParams(
        start_date=start_date,
        end_date=end_date,
        lead_source=lead_source,
        industry=industry,
    )
    warnings = []

    df = apply_filters(load_crm_funnel(), "lead_date", params)
    w = reliability_warning(df, "CRM funnel")
    if w:
        warnings.append(w)

    total = len(df)
    mqls  = int(df["reached_mql"].sum())
    sqls  = int(df["reached_sql"].sum())
    opps  = int(df["reached_opp"].sum())
    won   = int(df["reached_close"].sum())

    pipeline_value = float(df[df["outcome"] == "Closed Won"]["deal_value"].sum())
    avg_deal = float(df[df["outcome"] == "Closed Won"]["deal_value"].mean() or 0)
    avg_days = float(df["days_to_close"].dropna().mean() or 0)

    return {
        "total_leads": total,
        "mqls": mqls,
        "sqls": sqls,
        "opportunities": opps,
        "closed_won": won,
        "lead_to_mql_rate": round(mqls / max(total, 1) * 100, 2),
        "mql_to_sql_rate":  round(sqls / max(mqls, 1)  * 100, 2),
        "sql_to_opp_rate":  round(opps / max(sqls, 1)  * 100, 2),
        "opp_win_rate":     round(won  / max(opps, 1)  * 100, 2),
        "overall_win_rate": round(won  / max(total, 1) * 100, 2),
        "pipeline_closed_won": round(pipeline_value, 2),
        "avg_deal_value": round(avg_deal, 2),
        "avg_days_to_close": round(avg_days, 1),
        "warnings": warnings,
    }


@router.get("/by-source")
def funnel_by_source(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
):
    """
    Return funnel conversion rates broken down by lead source.
    """
    params = FilterParams(start_date=start_date, end_date=end_date)
    warnings = []

    df = apply_filters(load_crm_funnel(), "lead_date", params)
    w = reliability_warning(df, "CRM by source")
    if w:
        warnings.append(w)

    result = (
        df.groupby("lead_source")
        .agg(
            total_leads=("contact_id", "count"),
            mqls=("reached_mql", "sum"),
            sqls=("reached_sql", "sum"),
            opps=("reached_opp", "sum"),
            won=("reached_close", "sum"),
            pipeline_value=("deal_value", "sum"),
        )
        .reset_index()
    )
    result["win_rate_pct"] = (result["won"] / result["total_leads"].clip(lower=1) * 100).round(2)
    result["pipeline_value"] = result["pipeline_value"].round(2)

    return {"data": result.to_dict(orient="records"), "warnings": warnings}
