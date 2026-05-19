from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./portal.db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    COOKIE_SECURE: bool = True
    DS_API_URL: str = "http://dolphinscheduler:12345/dolphinscheduler"
    DS_ADMIN_USER: str = "admin"
    DS_ADMIN_PASSWORD: str = ""
    OM_API_URL: str = "http://localhost:8585"
    CORS_ORIGINS: list[str] | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 300
    ADMIN_INIT_PASSWORD: str = ""
    DQC_SERVICE_TOKEN: str = ""

    @field_validator("SECRET_KEY")
    @classmethod
    def _check_secret_key(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("SECRET_KEY 必须至少 16 个字符")
        return v

    class Config:
        env_file = ".env"


settings = Settings()
