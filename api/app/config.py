from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Configuration, environment-first.

    On the server, systemd loads /etc/mpsc/db.env (root-only, 0600) into the
    unit's environment, so nothing secret is ever written into this repo.
    Locally, point DATABASE_URL at a tunnel:

        ssh -L 5433:localhost:5432 ubuntu@152.67.31.231
        export DATABASE_URL=postgresql://mpsc@localhost:5433/bench
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://mpsc@localhost:5432/bench"
    public_catalog_cache_seconds: int = 60
    registered_document_root: str = "/srv/study/registered-documents"
    canonical_workshop_root: str = "/srv/study/workshop/mpsc-question-bankv2"
    paper_workbench_root: str = "/srv/study/private/paper-workbench"
    paper_archive_root: str = "/srv/study/papers/source"
    # Optional read-only mount visible inside the API service's filesystem namespace.
    pdf_library_archive_root: str = ""
    # Stage later saves until the previous guarded publication has synced.
    publication_serial_queue: bool = False
    pool_min: int = 2
    pool_max: int = 10
    # Vite dev server; production is same-origin behind Caddy so needs nothing.
    cors_origins: list[str] = ["http://localhost:5175", "http://localhost:5173"]
    # Separate from anonymous X-Device-Id; required for owner moderation APIs.
    admin_token: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    public_origin: str = "https://study.hawayu.in"
    mobile_redirect_uris: list[str] = ["finna://auth/callback"]
    mfa_encryption_key: str = ""
    mfa_enforce_staff: bool = False
    # Operator-managed exceptions use immutable account IDs, never request emails.
    staff_mfa_exempt_user_ids: str = ""
    study_desks_private_enabled: bool = False
    account_mail_enabled: bool = False
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_from: str = ''
    smtp_username: str = ''
    smtp_password: str = ''
    # Shared conservative attempt budget; defaults fit the selected free tier.
    smtp_daily_limit: int = Field(default=100,ge=0,le=1000000)
    smtp_monthly_limit: int = Field(default=3000,ge=0,le=30000000)
    # Deliberately opt in only after test-mode acceptance. Credentials alone do not enable checkout.
    razorpay_checkout_enabled: bool = False
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""


settings = Settings()
