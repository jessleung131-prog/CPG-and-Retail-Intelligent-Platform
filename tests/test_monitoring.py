"""Tests for monitoring and anomaly detection."""
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta


def _make_series(n=100, inject_anomaly_at=None):
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    values = 1000 + np.random.default_rng(0).normal(0, 50, n)
    if inject_anomaly_at is not None:
        values[inject_anomaly_at] = 9999  # Extreme outlier
    return pd.DataFrame({"date": dates, "revenue": values})


class TestFreshnessCheck:
    def test_fresh_data_ok(self):
        from monitoring.pipeline_monitor import check_freshness
        df = _make_series(100)
        # Make the last date today
        df.loc[df.index[-1], "date"] = datetime.now()
        result = check_freshness(df, "date", "test_table")
        assert result.status == "ok"

    def test_stale_data_warning(self):
        from monitoring.pipeline_monitor import check_freshness
        df = _make_series(50)
        # All dates in the past — last date is ~50 days ago
        result = check_freshness(df, "date", "test_table", warning_days=3, critical_days=7)
        assert result.status in ("warning", "critical")

    def test_empty_table_critical(self):
        from monitoring.pipeline_monitor import check_freshness
        df = pd.DataFrame({"date": [], "revenue": []})
        result = check_freshness(df, "date", "test_table")
        assert result.status == "critical"


class TestSchemaCheck:
    def test_schema_ok(self):
        from monitoring.pipeline_monitor import check_schema
        df = pd.DataFrame({"date": [], "revenue": [], "channel": []})
        result = check_schema(df, "test", ["date", "revenue", "channel"])
        assert result.status == "ok"

    def test_missing_column_critical(self):
        from monitoring.pipeline_monitor import check_schema
        df = pd.DataFrame({"date": [], "revenue": []})
        result = check_schema(df, "test", ["date", "revenue", "channel"])
        assert result.status == "critical"
        assert "channel" in result.detail


class TestAnomalyDetection:
    def test_detects_zscore_outlier(self):
        from monitoring.anomaly_detection import detect_anomalies
        df = _make_series(100, inject_anomaly_at=50)
        alerts = detect_anomalies(df, "date", ["revenue"], "test_table")
        assert any(a.check_type == "zscore" for a in alerts)

    def test_clean_data_no_critical(self):
        from monitoring.anomaly_detection import detect_anomalies
        rng = np.random.default_rng(42)
        dates = pd.date_range("2023-01-01", periods=100)
        values = 1000 + rng.normal(0, 20, 100)  # Tight distribution, no outliers
        df = pd.DataFrame({"date": dates, "revenue": values})
        alerts = detect_anomalies(df, "date", ["revenue"], "test_table")
        critical = [a for a in alerts if a.severity == "critical"]
        assert len(critical) == 0

    def test_alerts_ordered_by_severity(self):
        from monitoring.anomaly_detection import detect_anomalies
        df = _make_series(100, inject_anomaly_at=50)
        alerts = detect_anomalies(df, "date", ["revenue"], "test_table")
        if len(alerts) >= 2:
            order = {"critical": 0, "warning": 1, "info": 2}
            severities = [order[a.severity] for a in alerts]
            assert severities == sorted(severities)
