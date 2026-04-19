"""
/forecast — sales forecast endpoints.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Literal
import pandas as pd

from api.data_loader import load_online_sales, load_offline_sales
from api.filters import FilterParams, apply_filters, reliability_warning

router = APIRouter(prefix="/forecast", tags=["Forecast"])

MIN_ROWS_FOR_MODELING = 60  # Require at least 60 time periods to fit a model


@router.get("/sales")
def forecast_sales(
    channel:      Optional[str] = Query(None, description="Filter online sales by channel, e.g. DTC"),
    region:       Optional[str] = Query(None, description="Filter offline sales by region"),
    start_date:   Optional[str] = Query(None),
    end_date:     Optional[str] = Query(None),
    model:        str           = Query("prophet", description="prophet | xgboost"),
    horizon_days: int           = Query(90, ge=7, le=365),
    source:       str           = Query("online", description="online | offline"),
):
    """
    Run a sales forecast for the selected filters.

    Returns forecast values with confidence intervals,
    actual vs predicted on the test set, and model metrics.
    """
    from models.forecasting import run_forecast

    params = FilterParams(
        start_date=start_date,
        end_date=end_date,
        channel=channel,
        region=region,
    )
    warnings = []

    if source == "online":
        df = apply_filters(load_online_sales(), "date", params)
        date_col, target_col = "date", "revenue"
        daily = df.groupby(date_col, as_index=False)[target_col].sum()
    else:
        df = apply_filters(load_offline_sales(), "week_start", params)
        date_col, target_col = "week_start", "total_revenue"
        daily = df.groupby(date_col, as_index=False)[target_col].sum()

    w = reliability_warning(daily, f"{source} sales")
    if w:
        warnings.append(w)

    if len(daily) < MIN_ROWS_FOR_MODELING:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Only {len(daily)} data points after filtering. "
                f"At least {MIN_ROWS_FOR_MODELING} are required to fit a reliable model. "
                "Broaden your date range or remove dimension filters."
            ),
        )

    result = run_forecast(
        daily,
        date_col=date_col,
        target_col=target_col,
        model=model,
        horizon_days=horizon_days,
    )

    if result.confidence_warning:
        warnings.append(result.confidence_warning)

    forecast_records = result.forecast.copy()
    forecast_records["date"] = pd.to_datetime(forecast_records["date"]).dt.strftime("%Y-%m-%d")

    avp_records = result.actual_vs_predicted.copy()
    avp_records["date"] = pd.to_datetime(avp_records["date"]).dt.strftime("%Y-%m-%d")

    return {
        "model": result.model_name,
        "target": target_col,
        "train_end": result.train_end,
        "horizon_days": horizon_days,
        "metrics": result.metrics,
        "forecast": forecast_records.to_dict(orient="records"),
        "actual_vs_predicted": avp_records.to_dict(orient="records"),
        "warnings": warnings,
    }
