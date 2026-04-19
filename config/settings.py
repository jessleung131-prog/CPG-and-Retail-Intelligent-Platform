"""
Centralised settings loaded from environment variables / .env file.
All other modules import from here — never read os.environ directly.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root before anything else reads os.environ
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_FILE, override=True)


class _Settings:
    """Simple settings container backed by os.environ after load_dotenv."""

    @property
    def gcp_project_id(self):             return os.getenv("GCP_PROJECT_ID", "local")
    @property
    def gcp_region(self):                 return os.getenv("GCP_REGION", "us-central1")
    @property
    def google_application_credentials(self): return os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    @property
    def bq_dataset_raw(self):             return os.getenv("BQ_DATASET_RAW", "cpg_raw")
    @property
    def bq_dataset_staging(self):         return os.getenv("BQ_DATASET_STAGING", "cpg_staging")
    @property
    def bq_dataset_mart(self):            return os.getenv("BQ_DATASET_MART", "cpg_mart")
    @property
    def bq_dataset_ml(self):              return os.getenv("BQ_DATASET_ML", "cpg_ml")
    @property
    def bq_dataset_monitoring(self):      return os.getenv("BQ_DATASET_MONITORING", "cpg_monitoring")

    @property
    def api_host(self):                   return os.getenv("API_HOST", "0.0.0.0")
    @property
    def api_port(self):                   return int(os.getenv("API_PORT", "8000"))
    @property
    def api_secret_key(self):             return os.getenv("API_SECRET_KEY", "dev-secret-change-in-prod")

    @property
    def anthropic_api_key(self):          return os.getenv("ANTHROPIC_API_KEY", "")
    @property
    def claude_model(self):               return os.getenv("CLAUDE_MODEL", "claude-opus-4-6")

    @property
    def synthetic_start_date(self):       return os.getenv("SYNTHETIC_START_DATE", "2023-01-01")
    @property
    def synthetic_end_date(self):         return os.getenv("SYNTHETIC_END_DATE", "2024-12-31")
    @property
    def synthetic_seed(self):             return int(os.getenv("SYNTHETIC_SEED", "42"))

    @property
    def slack_webhook_url(self):          return os.getenv("SLACK_WEBHOOK_URL", "")


settings = _Settings()
