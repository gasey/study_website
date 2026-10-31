from pydantic_settings import BaseSettings, SettingsConfigDict


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
    paper_archive_root: str = "/srv/study/papers/source"
    pool_min: int = 2
    pool_max: int = 10
    # Vite dev server; production is same-origin behind Caddy so needs nothing.
    cors_origins: list[str] = ["http://localhost:5175", "http://localhost:5173"]
    # Separate from anonymous X-Device-Id; required for owner moderation APIs.
    admin_token: str = ""
    public_origin: str = "https://study.hawayu.in"
    mfa_encryption_key: str = ""
    mfa_enforce_staff: bool = False
    study_desks_private_enabled: bool = False
    account_mail_enabled: bool = False
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_from: str = ''
    smtp_username: str = ''
    smtp_password: str = ''
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""


settings = Settings()
