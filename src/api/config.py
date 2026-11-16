import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Liora Airlines API"
    VERSION: str = "0.0.1"

    # Sécurité
    API_KEY: str = os.getenv("API_KEY", "")
    API_KEY_NAME: str = "X-API-Key"

    # CORS : origines séparées par des virgules (vide = aucune)
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # Base de données PostgreSQL
    POSTGRES_USER: str = os.getenv("PG_USER", "batch")
    POSTGRES_PASSWORD: str = os.getenv("PG_PASSWORD", None)
    POSTGRES_HOST: str = os.getenv("PG_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("PG_PORT", "5432")
    POSTGRES_DB: str = os.getenv("PG_DB", "airline")

    # Modèle Scikit-Learn
    MODEL_PATH: str = os.getenv("MODEL_PATH", "/app/workspace/models/model.joblib")

    @property
    def cors_origins(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
