"""
Master synthetic data generator.

Runs all four data streams and saves output to data/ as Parquet files.

Usage:
    python synthetic_data/generate_all.py

Output files:
    data/online_sales.parquet
    data/offline_sales.parquet
    data/crm_funnel.parquet
    data/media_spend.parquet
"""
import sys
import time
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synthetic_data import online_sales, offline_sales, crm_funnel, media_spend
from config import settings


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"


def run():
    OUTPUT_DIR.mkdir(exist_ok=True)

    start_date = settings.synthetic_start_date
    end_date = settings.synthetic_end_date
    seed = settings.synthetic_seed

    generators = [
        ("online_sales",  online_sales.generate,  "Daily online sales by channel and category"),
        ("offline_sales", offline_sales.generate,  "Weekly offline POS data by region and store format"),
        ("crm_funnel",    crm_funnel.generate,     "CRM funnel contacts from lead through close"),
        ("media_spend",   media_spend.generate,    "Weekly multi-channel media spend and performance"),
    ]

    print(f"Generating synthetic data: {start_date} → {end_date}  (seed={seed})\n")
    summary = {}

    for name, fn, description in generators:
        t0 = time.time()
        print(f"  [{name}]  {description}...")
        df = fn(start_date=start_date, end_date=end_date, seed=seed)
        path = OUTPUT_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
        elapsed = time.time() - t0
        summary[name] = {"rows": len(df), "columns": len(df.columns), "path": str(path)}
        print(f"    -> {len(df):,} rows × {len(df.columns)} cols  saved to {path}  ({elapsed:.1f}s)")

    print("\nDone. Summary:")
    for name, info in summary.items():
        print(f"  {name:<20} {info['rows']:>8,} rows  →  {info['path']}")


if __name__ == "__main__":
    run()
