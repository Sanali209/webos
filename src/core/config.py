from typing import List, Literal, Optional, Union

from pydantic import AnyHttpUrl, MongoDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "WebOS Framework"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = True
    ENVIRONMENT: Literal["local", "dev", "prod"] = "local"

    # Security
    SECRET_KEY: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # Database
    MONGO_URL: str = "mongodb://127.0.0.1:27017"
    MONGO_DB_NAME: str = "webos_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6380"  # Changed to 6380 to match docker-compose

    # MinIO / S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "webos-uploads"
    S3_REGION: str = "us-east-1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, env_file_encoding="utf-8"
    )

settings = Settings()
