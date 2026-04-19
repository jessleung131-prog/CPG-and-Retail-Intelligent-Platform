"""
Sales forecasting module.

Supports two model backends selectable at runtime:
  - Prophet   (good for strong seasonality, holidays, interpretability)
  - XGBoost   (good for complex interactions, tabular features)

Both enforce chronological splits via models.splitter.
Output is a standardised ForecastResult dataclass.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


@dataclass
class ForecastResult:
    model_name: str
    target: str
    forecast_horizon_days: int
    train_end: str
    metrics: dict[str, float]              # mape, rmse, r2 on validation set
    forecast: pd.DataFrame                 # date, yhat, yhat_lower, yhat_upper
    actual_vs_predicted: pd.DataFrame      # date, actual, predicted (test set)
    confidence_warning: str | None = None  # populated if confidence is low


# ─── Prophet ─────────────────────────────────────────────────────────────────

def _run_prophet(
    train: pd.DataFrame,
    test: pd.DataFrame,
    date_col: str,
    target_col: str,
    horizon_days: int,
    regressors: list[str],
) -> ForecastResult:
    from prophet import Prophet

    df_train = train[[date_col, target_col] + regressors].rename(
        columns={date_col: "ds", target_col: "y"}
    )

    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.90,
    )
    for reg in regressors:
        m.add_regressor(reg)

    m.fit(df_train)

    # Validation metrics
    df_test = test[[date_col, target_col] + regressors].rename(
        columns={date_col: "ds", target_col: "y"}
    )
    val_pred = m.predict(df_test[["ds"] + regressors])
    actual = df_test["y"].values
    predicted = val_pred["yhat"].values

    metrics = _compute_metrics(actual, predicted)

    # Future forecast
    future = m.make_future_dataframe(periods=horizon_days)
    for reg in regressors:
        future[reg] = 0.0  # Zero out regressors for future (can be overridden)
    forecast_df = m.predict(future).tail(horizon_days)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    forecast_df = forecast_df.rename(columns={"ds": "date"})

    avp = pd.DataFrame(
        {"date": df_test["ds"].values, "actual": actual, "predicted": predicted}
    )

    warning = _confidence_warning(metrics)

    return ForecastResult(
        model_name="Prophet",
        target=target_col,
        forecast_horizon_days=horizon_days,
        train_end=str(train[date_col].max()),
        metrics=metrics,
        forecast=forecast_df,
        actual_vs_predicted=avp,
        confidence_warning=warning,
    )


# ─── XGBoost ─────────────────────────────────────────────────────────────────

def _build_features(df: pd.DataFrame, date_col: str, extra_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["day_of_week"]  = df[date_col].dt.dayofweek
    df["day_of_year"]  = df[date_col].dt.dayofyear
    df["week_of_year"] = df[date_col].dt.isocalendar().week.astype(int)
    df["month"]        = df[date_col].dt.month
    df["quarter"]      = df[date_col].dt.quarter
    df["year"]         = df[date_col].dt.year
    df["sin_doy"]      = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["cos_doy"]      = np.cos(2 * np.pi * df["day_of_year"] / 365)
    return df


def _run_xgboost(
    train: pd.DataFrame,
    test: pd.DataFrame,
    date_col: str,
    target_col: str,
    horizon_days: int,
    regressors: list[str],
) -> ForecastResult:
    import xgboost as xgb

    feature_cols = [
        "day_of_week", "day_of_year", "week_of_year", "month", "quarter", "year",
        "sin_doy", "cos_doy",
    ] + regressors

    train_f = _build_features(train, date_col, regressors)
    test_f  = _build_features(test,  date_col, regressors)

    X_train = train_f[feature_cols].fillna(0)
    y_train = train_f[target_col]
    X_test  = test_f[feature_cols].fillna(0)
    y_test  = test_f[target_col].values

    model = xgb.XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    predicted = model.predict(X_test)

    metrics = _compute_metrics(y_test, predicted)

    # Build future dates for forecast
    last_date = pd.to_datetime(test[date_col].max())
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon_days)
    future_df = pd.DataFrame({date_col: future_dates})
    for reg in regressors:
        future_df[reg] = 0.0
    future_f = _build_features(future_df, date_col, regressors)
    X_future = future_f[feature_cols].fillna(0)
    yhat_future = model.predict(X_future)

    # Naive confidence interval (±15 % based on train residuals std)
    residual_std = np.std(y_train.values - model.predict(X_train))
    forecast_df = pd.DataFrame(
        {
            "date": future_dates,
            "yhat": yhat_future,
            "yhat_lower": yhat_future - 1.645 * residual_std,
            "yhat_upper": yhat_future + 1.645 * residual_std,
        }
    )

    avp = pd.DataFrame(
        {"date": test_f[date_col].values, "actual": y_test, "predicted": predicted}
    )

    warning = _confidence_warning(metrics)

    return ForecastResult(
        model_name="XGBoost",
        target=target_col,
        forecast_horizon_days=horizon_days,
        train_end=str(train[date_col].max()),
        metrics=metrics,
        forecast=forecast_df,
        actual_vs_predicted=avp,
        confidence_warning=warning,
    )


# ─── Shared utilities ─────────────────────────────────────────────────────────

def _compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    from sklearn.metrics import r2_score

    actual = np.array(actual, dtype=float)
    predicted = np.array(predicted, dtype=float)

    nonzero = actual != 0
    mape = float(np.mean(np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])) * 100)
    rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
    r2   = float(r2_score(actual, predicted))

    return {"mape": round(mape, 3), "rmse": round(rmse, 2), "r2": round(r2, 4)}


def _confidence_warning(metrics: dict) -> str | None:
    if metrics["mape"] > 20:
        return f"Model MAPE is {metrics['mape']:.1f}% — forecasts have high uncertainty. Consider expanding the date range or reviewing data quality."
    if metrics["r2"] < 0.50:
        return f"Low R² ({metrics['r2']:.2f}) — the model explains less than 50% of variance. Results should be interpreted with caution."
    return None


# ─── Public API ───────────────────────────────────────────────────────────────

def run_forecast(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    model: Literal["prophet", "xgboost"] = "prophet",
    horizon_days: int = 90,
    regressors: list[str] | None = None,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> ForecastResult:
    """
    Fit a forecasting model and return predictions + metrics.

    Args:
        df:           Time-series DataFrame, one row per time period.
        date_col:     Name of the date column.
        target_col:   Name of the column to forecast.
        model:        "prophet" or "xgboost".
        horizon_days: Number of days to forecast beyond the data end.
        regressors:   Optional list of external regressor column names.
        train_frac:   Fraction of time range used for training (default 0.70).
        val_frac:     Fraction used for validation (default 0.15).

    Returns:
        ForecastResult with metrics, forecast, and actual_vs_predicted.
    """
    from models.splitter import split

    regressors = regressors or []
    splits = split(df, date_col, train_frac=train_frac, val_frac=val_frac)

    print(splits.summary())

    if model == "prophet":
        return _run_prophet(
            splits.train, splits.test, date_col, target_col, horizon_days, regressors
        )
    elif model == "xgboost":
        return _run_xgboost(
            splits.train, splits.test, date_col, target_col, horizon_days, regressors
        )
    else:
        raise ValueError(f"Unknown model '{model}'. Choose 'prophet' or 'xgboost'.")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    # Quick smoke test with synthetic data
    data_path = Path("data/online_sales.parquet")
    if not data_path.exists():
        print("Run synthetic_data/generate_all.py first to generate data.")
        sys.exit(1)

    df = pd.read_parquet(data_path)
    # Aggregate to daily total revenue for a simple test
    daily = df.groupby("date", as_index=False)["revenue"].sum()
    daily["date"] = pd.to_datetime(daily["date"])

    result = run_forecast(daily, "date", "revenue", model="prophet", horizon_days=30)
    print(f"\nModel:   {result.model_name}")
    print(f"MAPE:    {result.metrics['mape']:.2f}%")
    print(f"RMSE:    {result.metrics['rmse']:,.0f}")
    print(f"R²:      {result.metrics['r2']:.4f}")
    if result.confidence_warning:
        print(f"WARNING: {result.confidence_warning}")
    print(f"\nForecast (first 5 rows):\n{result.forecast.head()}")
