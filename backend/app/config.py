from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./stock_analysis.db"

    # SEC EDGAR
    SEC_USER_AGENT: str = "StockAnalysis contact@example.com"

    # Google Gemini
    GEMINI_API_KEY: str = ""

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
