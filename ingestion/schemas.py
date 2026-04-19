"""
BigQuery table schemas for all layers.

raw      → raw ingest (append-only, no transforms)
staging  → cleaned + typed
mart     → business-ready aggregates
ml       → feature tables for models
monitoring → pipeline health and model metrics
"""
from google.cloud import bigquery

# ─── RAW SCHEMAS ─────────────────────────────────────────────────────────────

RAW_ONLINE_SALES = [
    bigquery.SchemaField("ingested_at",      "TIMESTAMP"),
    bigquery.SchemaField("date",             "DATE"),
    bigquery.SchemaField("channel",          "STRING"),
    bigquery.SchemaField("category",         "STRING"),
    bigquery.SchemaField("orders",           "INTEGER"),
    bigquery.SchemaField("revenue",          "FLOAT"),
    bigquery.SchemaField("avg_order_value",  "FLOAT"),
    bigquery.SchemaField("units_sold",       "INTEGER"),
    bigquery.SchemaField("returns",          "INTEGER"),
    bigquery.SchemaField("return_rate",      "FLOAT"),
    bigquery.SchemaField("promo_flag",       "INTEGER"),
]

RAW_OFFLINE_SALES = [
    bigquery.SchemaField("ingested_at",        "TIMESTAMP"),
    bigquery.SchemaField("week_start",         "DATE"),
    bigquery.SchemaField("region",             "STRING"),
    bigquery.SchemaField("store_format",       "STRING"),
    bigquery.SchemaField("category",           "STRING"),
    bigquery.SchemaField("active_stores",      "INTEGER"),
    bigquery.SchemaField("total_revenue",      "FLOAT"),
    bigquery.SchemaField("revenue_per_store",  "FLOAT"),
    bigquery.SchemaField("units_sold",         "INTEGER"),
    bigquery.SchemaField("avg_selling_price",  "FLOAT"),
    bigquery.SchemaField("promo_flag",         "INTEGER"),
    bigquery.SchemaField("distribution_pct",   "FLOAT"),
]

RAW_CRM_FUNNEL = [
    bigquery.SchemaField("ingested_at",       "TIMESTAMP"),
    bigquery.SchemaField("contact_id",        "STRING"),
    bigquery.SchemaField("lead_source",       "STRING"),
    bigquery.SchemaField("industry",          "STRING"),
    bigquery.SchemaField("lead_date",         "DATE"),
    bigquery.SchemaField("mql_date",          "DATE"),
    bigquery.SchemaField("sql_date",          "DATE"),
    bigquery.SchemaField("opportunity_date",  "DATE"),
    bigquery.SchemaField("close_date",        "DATE"),
    bigquery.SchemaField("outcome",           "STRING"),
    bigquery.SchemaField("deal_value",        "FLOAT"),
    bigquery.SchemaField("days_to_close",     "INTEGER"),
    bigquery.SchemaField("reached_mql",       "INTEGER"),
    bigquery.SchemaField("reached_sql",       "INTEGER"),
    bigquery.SchemaField("reached_opp",       "INTEGER"),
    bigquery.SchemaField("reached_close",     "INTEGER"),
]

RAW_MEDIA_SPEND = [
    bigquery.SchemaField("ingested_at",           "TIMESTAMP"),
    bigquery.SchemaField("week_start",            "DATE"),
    bigquery.SchemaField("channel",               "STRING"),
    bigquery.SchemaField("spend",                 "FLOAT"),
    bigquery.SchemaField("impressions",           "INTEGER"),
    bigquery.SchemaField("clicks",                "INTEGER"),
    bigquery.SchemaField("conversions",           "INTEGER"),
    bigquery.SchemaField("cpm",                   "FLOAT"),
    bigquery.SchemaField("ctr",                   "FLOAT"),
    bigquery.SchemaField("cvr",                   "FLOAT"),
    bigquery.SchemaField("cpc",                   "FLOAT"),
    bigquery.SchemaField("cpa",                   "FLOAT"),
    bigquery.SchemaField("roas",                  "FLOAT"),
    bigquery.SchemaField("adstocked_spend",       "FLOAT"),
    bigquery.SchemaField("saturated_spend",       "FLOAT"),
    bigquery.SchemaField("incremental_revenue",   "FLOAT"),
    bigquery.SchemaField("media_contribution_pct","FLOAT"),
]

# ─── MONITORING SCHEMAS ───────────────────────────────────────────────────────

MONITORING_PIPELINE_RUNS = [
    bigquery.SchemaField("run_id",          "STRING"),
    bigquery.SchemaField("run_at",          "TIMESTAMP"),
    bigquery.SchemaField("table_name",      "STRING"),
    bigquery.SchemaField("rows_ingested",   "INTEGER"),
    bigquery.SchemaField("status",          "STRING"),   # success | failed | warning
    bigquery.SchemaField("error_message",   "STRING"),
    bigquery.SchemaField("duration_secs",   "FLOAT"),
]

MONITORING_DATA_QUALITY = [
    bigquery.SchemaField("check_id",        "STRING"),
    bigquery.SchemaField("checked_at",      "TIMESTAMP"),
    bigquery.SchemaField("table_name",      "STRING"),
    bigquery.SchemaField("check_type",      "STRING"),   # null_rate | freshness | schema_drift | anomaly
    bigquery.SchemaField("column_name",     "STRING"),
    bigquery.SchemaField("metric_value",    "FLOAT"),
    bigquery.SchemaField("threshold",       "FLOAT"),
    bigquery.SchemaField("passed",          "BOOLEAN"),
    bigquery.SchemaField("severity",        "STRING"),   # info | warning | critical
    bigquery.SchemaField("root_cause_hint", "STRING"),
]

MONITORING_MODEL_METRICS = [
    bigquery.SchemaField("metric_id",       "STRING"),
    bigquery.SchemaField("recorded_at",     "TIMESTAMP"),
    bigquery.SchemaField("model_name",      "STRING"),
    bigquery.SchemaField("model_version",   "STRING"),
    bigquery.SchemaField("metric_name",     "STRING"),   # mape | rmse | r2 | coverage
    bigquery.SchemaField("metric_value",    "FLOAT"),
    bigquery.SchemaField("threshold",       "FLOAT"),
    bigquery.SchemaField("passed",          "BOOLEAN"),
]


# Registry: maps (dataset_key, table_name) → schema
SCHEMA_REGISTRY: dict[tuple[str, str], list[bigquery.SchemaField]] = {
    ("raw",        "online_sales"):        RAW_ONLINE_SALES,
    ("raw",        "offline_sales"):       RAW_OFFLINE_SALES,
    ("raw",        "crm_funnel"):          RAW_CRM_FUNNEL,
    ("raw",        "media_spend"):         RAW_MEDIA_SPEND,
    ("monitoring", "pipeline_runs"):       MONITORING_PIPELINE_RUNS,
    ("monitoring", "data_quality"):        MONITORING_DATA_QUALITY,
    ("monitoring", "model_metrics"):       MONITORING_MODEL_METRICS,
}
