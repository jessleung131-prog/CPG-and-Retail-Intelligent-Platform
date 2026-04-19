"""
Provision BigQuery datasets and tables for all platform layers.

Run once during initial GCP setup:
    python ingestion/create_datasets.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import bigquery
from config import settings
from ingestion.schemas import SCHEMA_REGISTRY


DATASETS = [
    settings.bq_dataset_raw,
    settings.bq_dataset_staging,
    settings.bq_dataset_mart,
    settings.bq_dataset_ml,
    settings.bq_dataset_monitoring,
]

# Dataset key → BQ dataset name
DATASET_KEY_MAP = {
    "raw":        settings.bq_dataset_raw,
    "staging":    settings.bq_dataset_staging,
    "mart":       settings.bq_dataset_mart,
    "ml":         settings.bq_dataset_ml,
    "monitoring": settings.bq_dataset_monitoring,
}


def create_datasets(client: bigquery.Client):
    for dataset_id in DATASETS:
        full_id = f"{settings.gcp_project_id}.{dataset_id}"
        dataset = bigquery.Dataset(full_id)
        dataset.location = settings.gcp_region
        client.create_dataset(dataset, exists_ok=True)
        print(f"  Dataset ready: {full_id}")


def create_tables(client: bigquery.Client):
    for (dataset_key, table_name), schema in SCHEMA_REGISTRY.items():
        dataset_id = DATASET_KEY_MAP[dataset_key]
        table_ref = f"{settings.gcp_project_id}.{dataset_id}.{table_name}"
        table = bigquery.Table(table_ref, schema=schema)

        # Partition raw/staging tables by date for cost efficiency
        if dataset_key in ("raw", "staging") and any(
            f.name in ("date", "week_start", "lead_date") for f in schema
        ):
            date_field = next(
                f.name for f in schema
                if f.name in ("date", "week_start", "lead_date")
            )
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field=date_field,
            )

        client.create_table(table, exists_ok=True)
        print(f"  Table ready: {table_ref}")


def main():
    client = bigquery.Client(project=settings.gcp_project_id)
    print(f"Project: {settings.gcp_project_id}  Region: {settings.gcp_region}\n")
    print("Creating datasets...")
    create_datasets(client)
    print("\nCreating tables...")
    create_tables(client)
    print("\nDone.")


if __name__ == "__main__":
    main()
