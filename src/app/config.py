"""Application configuration using Pydantic Settings."""


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Bug Reporting API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")  # nosec B104
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://buguser:bugpass@localhost:5432/bugreporting",
        alias="DATABASE_URL",
    )
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    # JWT Configuration
    jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_private_key_path: str = Field(
        default="./keys/private_key.pem", alias="JWT_PRIVATE_KEY_PATH"
    )
    jwt_public_key_path: str = Field(default="./keys/public_key.pem", alias="JWT_PUBLIC_KEY_PATH")

    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")  # Required
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS")
    max_login_attempts: int = Field(default=5, alias="MAX_LOGIN_ATTEMPTS")
    account_lockout_duration_minutes: int = Field(
        default=30, alias="ACCOUNT_LOCKOUT_DURATION_MINUTES"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")
    login_rate_limit_per_minute: int = Field(default=5, alias="LOGIN_RATE_LIMIT_PER_MINUTE")

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # Pagination
    default_page_size: int = Field(default=20, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")

    # File Upload
    max_upload_size_mb: int = Field(default=1, alias="MAX_UPLOAD_SIZE_MB")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["http://localhost:3000"]
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of allowed values."""
        allowed = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of: {', '.join(allowed)}")
        return v_upper

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"


# Global settings instance
settings = Settings()
