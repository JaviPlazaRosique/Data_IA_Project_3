from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Full URL (used in local dev via .env)
    DATABASE_URL: str = ""
    # Individual components (used in Cloud Run where password comes from Secret Manager)
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = ""

    # Firestore / Firebase — optional; empty string uses Application Default Credentials
    GOOGLE_CLOUD_PROJECT: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""  # path to service account JSON file

    @model_validator(mode="after")
    def validate_db_config(self) -> "Settings":
        has_full_url = bool(self.DATABASE_URL)
        has_components = all([self.DB_HOST, self.DB_NAME, self.DB_USER, self.DB_PASSWORD])
        if not has_full_url and not has_components:
            raise ValueError(
                "Database configuration is missing. "
                "Set DATABASE_URL or all of: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD"
            )
        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must be set (comma-separated list of allowed origins)")
        return self

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
