from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    FASTAPI_ENV: Literal["development"] | None = None
    PROJECT_NAME: str

    DATABASE_URL: str
    DEBUG: bool = False
    ENGINE_CHECK_SAME_THREAD: bool = True


settings = Settings()  # type: ignore[call-arg] # pyright: ignore[reportCallIssue]

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("settings %s", settings)
