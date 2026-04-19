"""
Integration tests for FastAPI endpoints.

These tests run against local Parquet data (no GCP needed).
Generate data first: python synthetic_data/generate_all.py
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_AVAILABLE = all(
    (DATA_DIR / f).exists()
    for f in ["online_sales.parquet", "offline_sales.parquet",
              "crm_funnel.parquet", "media_spend.parquet"]
)


@pytest.fixture(scope="module")
def client():
    from api.main import app
    from api import data_loader
    data_loader.clear_cache()
    return TestClient(app)


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Synthetic data not generated yet")
class TestHealthEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Synthetic data not generated yet")
class TestKPIEndpoints:
    def test_kpi_summary(self, client):
        r = client.get("/kpis/summary")
        assert r.status_code == 200
        data = r.json()
        assert "total_revenue" in data
        assert "blended_roas" in data
        assert "warnings" in data
        assert data["total_revenue"] > 0

    def test_kpi_summary_with_date_filter(self, client):
        r = client.get("/kpis/summary?start_date=2023-01-01&end_date=2023-06-30")
        assert r.status_code == 200

    def test_kpi_trend_weekly(self, client):
        r = client.get("/kpis/trend?granularity=weekly")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert len(data["data"]) > 0

    def test_kpi_trend_monthly(self, client):
        r = client.get("/kpis/trend?granularity=monthly")
        assert r.status_code == 200


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Synthetic data not generated yet")
class TestCRMEndpoints:
    def test_funnel_summary(self, client):
        r = client.get("/crm/funnel")
        assert r.status_code == 200
        data = r.json()
        assert "total_leads" in data
        assert "win_rate_pct" in data
        assert data["mqls"] <= data["total_leads"]

    def test_funnel_by_source(self, client):
        r = client.get("/crm/by-source")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert len(data["data"]) > 0

    def test_funnel_filter_reduces_reliability_warning(self, client):
        # Filter to a very narrow date range — should trigger a warning
        r = client.get("/crm/funnel?start_date=2023-01-01&end_date=2023-01-03")
        assert r.status_code == 200
        # A narrow date range may produce a warning about low data volume
        data = r.json()
        assert "warnings" in data


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Synthetic data not generated yet")
class TestAttributionEndpoints:
    def test_spend_efficiency(self, client):
        r = client.get("/attribution/spend-efficiency")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert len(data["data"]) > 0
        # Each row should have ROAS
        for row in data["data"]:
            assert "avg_roas" in row
