from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str
    TEST_DATABASE_URL: str = (
        "mysql+aiomysql://nutrition_user:nutrition_pass@localhost:3307/nutrition_test_db"
    )
    SECRET_KEY: str
    ANTHROPIC_API_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
