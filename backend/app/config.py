from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    admin_password: str = "changeme"
    submission_daily_limit: int = 5

    model_config = {"env_file": ".env"}


settings = Settings()
