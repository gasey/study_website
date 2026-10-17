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
    pool_min: int = 2
    pool_max: int = 10
    # Vite dev server; production is same-origin behind Caddy so needs nothing.
    cors_origins: list[str] = ["http://localhost:5175", "http://localhost:5173"]


settings = Settings()
