from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = ""
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = ""

    GOOGLE_CLOUD_PROJECT: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_AUTH_PROJECT_ID: str = ""

    BIGQUERY_PROJECT_ID: str = ""
    BIGQUERY_ANALYTICS_DATASET: str = "recomendacion_planes"
    BIGQUERY_MARTS_DATASET: str = "recomendacion_planes_marts"

    @model_validator(mode="after")
    def validate_config(self) -> "Settings":
        has_full_url = bool(self.DATABASE_URL)
        has_components = all([self.DB_HOST, self.DB_NAME, self.DB_USER, self.DB_PASSWORD])
        if not has_full_url and not has_components:
            raise ValueError(
                "Database config missing. Set DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD."
            )
        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must be set")
        return self

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
