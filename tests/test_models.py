"""Tests for forecasting model and splitter."""
import numpy as np
import pandas as pd
import pytest


def _make_daily_revenue(n_days=200):
    dates = pd.date_range("2023-01-01", periods=n_days, freq="D")
    rng = np.random.default_rng(42)
    revenue = 10_000 + 500 * np.sin(2 * np.pi * np.arange(n_days) / 30) + rng.normal(0, 300, n_days)
    return pd.DataFrame({"date": dates, "revenue": revenue.clip(min=0)})


class TestChronologicalSplitter:
    def test_no_overlap(self):
        from models.splitter import split
        df = _make_daily_revenue(200)
        s = split(df, "date")
        assert s.train["date"].max() < s.validation["date"].min()
        assert s.validation["date"].max() < s.test["date"].min()

    def test_correct_fractions(self):
        from models.splitter import split
        df = _make_daily_revenue(200)
        s = split(df, "date", train_frac=0.70, val_frac=0.15)
        total = len(s.train) + len(s.validation) + len(s.test)
        assert total == len(df)
        assert len(s.train) > len(s.test)

    def test_invalid_fracs_raises(self):
        from models.splitter import split
        df = _make_daily_revenue(100)
        with pytest.raises(ValueError):
            split(df, "date", train_frac=0.80, val_frac=0.30)  # sum >= 1


class TestForecasting:
    def test_xgboost_returns_result(self):
        from models.forecasting import run_forecast
        df = _make_daily_revenue(200)
        result = run_forecast(df, "date", "revenue", model="xgboost", horizon_days=14)
        assert result.model_name == "XGBoost"
        assert len(result.forecast) == 14
        assert "mape" in result.metrics
        assert "rmse" in result.metrics
        assert "r2" in result.metrics

    def test_forecast_future_dates_are_after_train_end(self):
        from models.forecasting import run_forecast
        df = _make_daily_revenue(200)
        result = run_forecast(df, "date", "revenue", model="xgboost", horizon_days=30)
        forecast_dates = pd.to_datetime(result.forecast["date"])
        train_end = pd.Timestamp(result.train_end)
        assert (forecast_dates > train_end).all()

    def test_avp_has_actual_and_predicted(self):
        from models.forecasting import run_forecast
        df = _make_daily_revenue(200)
        result = run_forecast(df, "date", "revenue", model="xgboost", horizon_days=14)
        assert "actual" in result.actual_vs_predicted.columns
        assert "predicted" in result.actual_vs_predicted.columns
