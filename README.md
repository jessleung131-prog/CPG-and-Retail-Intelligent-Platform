# CPG & Retail Intelligent Platform

A production-oriented analytics platform for CPG and retail clients operating across eCommerce and brick-and-mortar channels. Built on GCP with Python and FastAPI.

## What It Does

| Layer | Capability |
|---|---|
| **Data Ingestion** | Ingest CRM, sales, and marketing data into BigQuery (batch + incremental) |
| **Modeling** | Sales forecasting (Prophet/XGBoost) + MMM channel contribution & incremental ROI |
| **Dashboard API** | FastAPI endpoints with dynamic filtering, confidence warnings, actual vs. predicted |
| **Monitoring** | Anomaly detection, data freshness, schema drift, model degradation alerts |
| **Insights** | Claude-powered automatic business insight generation from dashboard outputs |
| **Exec Decks** | Auto-generated PPTX executive presentations for marketing and sales leadership |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│   CRM Systems · eCommerce Platform · POS / Offline · Ad Platforms│
└────────────────────────────┬────────────────────────────────────┘
                             │ batch / incremental
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BIGQUERY LAYERS                             │
│  raw → staging → mart → ml → monitoring                        │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌──────────────────────┐
│   ML MODELS      │       │   MONITORING          │
│  · Forecasting   │       │  · Anomaly detection  │
│  · MMM / LMM     │       │  · Freshness checks   │
│  · Attribution   │       │  · Schema drift       │
└────────┬─────────┘       │  · Model degradation  │
         │                 └──────────┬─────────────┘
         ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI DASHBOARD API                        │
│  /forecast · /attribution · /kpis · /anomalies · /health        │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────┐         ┌──────────────────────┐
│  INSIGHTS LAYER     │         │  DECK GENERATION      │
│  Claude API         │────────▶│  python-pptx          │
│  · Trends / Risks   │         │  · Exec summary       │
│  · Recommendations  │         │  · Channel highlights  │
│  · Business summary │         │  · Forecast outlook   │
└─────────────────────┘         └──────────────────────┘
```

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/YOUR_USERNAME/cpg-retail-platform.git
cd cpg-retail-platform

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY for insights/decks
# GCP credentials are only needed to push data to BigQuery
```

### 3. Generate synthetic data

```bash
python synthetic_data/generate_all.py
# Outputs 2 years of data to data/ directory
# online_sales.parquet, offline_sales.parquet, crm_funnel.parquet, media_spend.parquet
```

### 4. Run the API

```bash
uvicorn api.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 5. Generate an insight report + deck

```bash
python insights/generate_insights.py
python deck_generation/generate_deck.py
# Outputs to outputs/insights_report.json and outputs/executive_deck.pptx
```

---

## Module Overview

| Directory | Description |
|---|---|
| `synthetic_data/` | Generates 2 years of realistic CPG/retail synthetic data |
| `ingestion/` | BigQuery schema definitions and data loaders |
| `models/` | Sales forecasting and MMM models with chronological splits |
| `api/` | FastAPI application — dashboard endpoints and filter warnings |
| `monitoring/` | Anomaly detection, freshness checks, alerting |
| `insights/` | Claude API integration for automatic insight generation |
| `deck_generation/` | Executive PPTX deck builder |
| `config/` | Shared configuration and BigQuery dataset settings |
| `tests/` | Pytest test suite |
| `docs/` | Data dictionary and additional architecture notes |

---

## Synthetic Data

The platform ships with a realistic 2-year synthetic dataset (Jan 2023 – Dec 2024) covering:

- **Online sales** — daily orders, revenue, AOV by channel (DTC, Amazon, Walmart.com) with seasonality and promo lifts
- **Offline sales** — weekly store-level POS data by region with distribution expansion events
- **CRM funnel** — lead → MQL → SQL → opportunity → closed-won pipeline with realistic conversion rates and lag
- **Media spend** — weekly channel spend (paid search, paid social, display, TV, email, influencer) with simulated ROI and adstock effects

---

## GCP Setup (Production)

To connect to a live GCP project:

1. Create a GCP project and enable the BigQuery API
2. Create a service account with BigQuery Admin role
3. Download the JSON key and set `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
4. Set `GCP_PROJECT_ID` in `.env`
5. Run `python ingestion/create_datasets.py` to provision BigQuery datasets
6. Run `python ingestion/load_to_bigquery.py` to load synthetic data

---

## Tech Stack

- **Cloud:** GCP (BigQuery, Cloud Run)
- **Data:** Python, pandas, pyarrow
- **Models:** Prophet, XGBoost, LightweightMMM, scikit-learn
- **API:** FastAPI, Uvicorn
- **Intelligence:** Anthropic Claude API (`claude-opus-4-6`)
- **Decks:** python-pptx
- **Tests:** pytest

---

## License

MIT
