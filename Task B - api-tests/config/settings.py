import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    env: str
    base_url: str

    business1_email: str
    business1_password: str
    courier1_email: str
    courier1_password: str

    business2_email: str
    business2_password: str
    courier2_email: str
    courier2_password: str


def _find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _validate_required_values(values: dict) -> None:
    required_keys = [
        "BASE_URL",
        "BUSINESS1_EMAIL",
        "BUSINESS1_PASSWORD",
        "COURIER1_EMAIL",
        "COURIER1_PASSWORD",
        "BUSINESS2_EMAIL",
        "BUSINESS2_PASSWORD",
        "COURIER2_EMAIL",
        "COURIER2_PASSWORD",
    ]

    missing_keys = [key for key in required_keys
                    if not values.get(key) or not values[key].strip()
                    ]

    if missing_keys:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_keys)}")


def _validate_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"Invalid URL configuration: {base_url}")
    return base_url.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = os.getenv("ENV", "qa").strip().lower()
    supported_envs = {"qa", "dev"}
    if env not in supported_envs:
        raise RuntimeError(f"ENV {env} not supported. Set qa|dev")
    project_root = _find_project_root()

    env_file = project_root / f".env.{env}"
    values = dict(dotenv_values(env_file)) if env_file.is_file() else {}
    values = {key: value for key, value in values.items() if value is not None}
    _validate_required_values(values)

    base_url = _validate_base_url(values["BASE_URL"].strip())

    return Settings(
        env=env,
        base_url=base_url,
        business1_email=values["BUSINESS1_EMAIL"].strip(),
        business1_password=values["BUSINESS1_PASSWORD"].strip(),
        courier1_email=values["COURIER1_EMAIL"].strip(),
        courier1_password=values["COURIER1_PASSWORD"].strip(),
        business2_email=values["BUSINESS2_EMAIL"].strip(),
        business2_password=values["BUSINESS2_PASSWORD"].strip(),
        courier2_email=values["COURIER2_EMAIL"].strip(),
        courier2_password=values["COURIER2_PASSWORD"].strip(),
    )
