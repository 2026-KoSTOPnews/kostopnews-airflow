from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "KoSTOPnews"

    # PostgreSQL
    POSTGRES_HOST: str = "postgres"
    POSTGRES_DB: str = "airflow"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "root"
    POSTGRES_PORT: int = 5432

    MODEL_VERSION: str = "gemini-2.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()