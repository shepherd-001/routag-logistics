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

    business_email: str
    business_password: str

    courier_email: str
    courier_password: str


def _find_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _validate_required_values(values: dict) -> None:
    required_keys = [
        "BASE_URL",
        "BUSINESS_EMAIL",
        "BUSINESS_PASSWORD",
        "COURIER_EMAIL",
        "COURIER_PASSWORD",
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
        business_email=values["BUSINESS_EMAIL"].strip(),
        business_password=values["BUSINESS_PASSWORD"].strip(),
        courier_email=values["COURIER_EMAIL"].strip(),
        courier_password=values["COURIER_PASSWORD"].strip(),
    )
