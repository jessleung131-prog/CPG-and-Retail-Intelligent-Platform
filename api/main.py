"""
FastAPI application entry point.

Run locally:
    uvicorn api.main:app --reload --port 8000

Interactive docs:
    http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import kpis, forecast, attribution, crm

app = FastAPI(
    title="CPG & Retail Intelligence Platform",
    description=(
        "Marketing and sales analytics API for CPG and retail clients. "
        "Supports sales forecasting, MMM channel attribution, CRM funnel analytics, "
        "and KPI dashboards across online and offline channels."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router)
app.include_router(forecast.router)
app.include_router(attribution.router)
app.include_router(crm.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "platform": "CPG & Retail Intelligence Platform",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
