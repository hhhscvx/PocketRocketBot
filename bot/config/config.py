from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    MIN_AVAILABLE_ENERGY: int = 100
    SLEEP_BY_MIN_ENERGY: list[int] = [450, 800]

    RANDOM_TAPS_COUNT: list[int] = [50, 200]
    SLEEP_BETWEEN_TAP: list[int] = [10, 25]

    APPLY_DAILY_ENERGY: bool = True
    APPLY_DAILY_TURBO: bool = True

    AUTO_UPGRADE_TAP: bool = True
    AUTO_UPGRADE_ENERGY: bool = True
    AUTO_UPGRADE_CHARGE: bool = True
    AUTO_UPGRADE_AUTOBOT: bool = True

    MAX_TAP_LEVEL: int = 8
    MAX_ENERGY_LEVEL: int = 8
    MAX_CHARGE_LEVEL: int = 8
    MAX_AUTOBOT_LEVEL: int = 8

    SHIP_TO_EQUIP: str = "0df2f67c-7ff2-4732-a0ca-17a635731b1b"

    USE_PROXY_FROM_FILE: bool = False

    WORKDIR: str = "sessions/"


settings = Settings()
