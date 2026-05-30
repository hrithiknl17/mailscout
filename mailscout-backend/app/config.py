from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://mailscout:mailscout@localhost:5432/mailscout"
    redis_url: str = "redis://localhost:6379"
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_anon_key: str = "placeholder"
    supabase_service_role_key: str = "placeholder"
    mailscout_helo_domain: str = "mailscout.dev"
    mailscout_sender_email: str = "verify@mailscout.dev"
    mailscout_free_tier_limit: int = 100
    smtp_timeout_seconds: int = 10
    smtp_concurrent_workers: int = 20
    log_level: str = "INFO"
    app_version: str = "1.0.0"
    frontend_url: str = ""


settings = Settings()
