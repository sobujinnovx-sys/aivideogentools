from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./aivideo.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./storage"
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    CREDITS_5S: int = 10
    CREDITS_10S: int = 20
    CREDITS_15S: int = 30

    DEFAULT_MODEL: str = "wan2.1"

    class Config:
        env_file = ".env"


settings = Settings()
