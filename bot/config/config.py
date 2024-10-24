from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    MIN_AVAILABLE_ENERGY: int = 100
    SLEEP_BY_MIN_ENERGY: list[int] = [250, 400]

    RANDOM_TAPS_COUNT: list[int] = [50, 200]
    SLEEP_BETWEEN_TAP: list[int] = [10, 25]

    APPLY_DAILY_ENERGY: bool = True
    APPLY_DAILY_TURBO: bool = True

    AUTO_UPGRADE_TAP: bool = True
    AUTO_UPGRADE_ENERGY: bool = True
    AUTO_UPGRADE_CHARGE: bool = True

    MAX_TAP_LEVEL: int = 7
    MAX_ENERGY_LEVEL: int = 7
    MAX_CHARGE_LEVEL: int = 3

    RELOGIN_DELAY: list[int] = [5, 7]

    USE_PROXY_FROM_FILE: bool = False

    WORKDIR: str = "sessions/"


settings = Settings()
