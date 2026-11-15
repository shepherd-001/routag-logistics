import json
import logging
import sys
from typing import Any

from config.settings import get_settings


def get_logger(name: str = "api_test_logger") -> logging.Logger:
    settings = get_settings()

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers.
    if any(getattr(handler, "_api_test_handler", False) for handler in logger.handlers):
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Identify this handler.
    console_handler._api_test_handler = True

    logger.addHandler(console_handler)
    logger.propagate = False

    logger.info("Logger initialized | Environment: %s", settings.env)

    return logger


class ApiLogger:

    def __init__(self, name: str = "api"):
        self.logger = get_logger(name)

    @staticmethod
    def _format(value: Any) -> str:
        if value is None:
            return "None"

        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=4, ensure_ascii=False, default=str)
        return str(value)

    def log_request(self, method: str, url: str, headers: dict | None = None, body: Any = None) -> None:
        self.logger.info(
            "\n%s | %s\n"
            "Headers:\n%s\n"
            "Request Body:\n%s\n",
            method.upper(), url, self._format(headers or {}), self._format(body))

    def log_response(self, status_code: int, url: str, headers: dict | None = None, body: Any = None, ) -> None:
        self.logger.info(
            "\n%s ==> %s\n"
            "Headers:\n%s\n"
            "Response Body:\n%s\n",
            url, status_code, self._format(headers or {}), self._format(body))

    def log_error(self, method: str, url: str, error: Exception) -> None:
        self.logger.exception(
            "\n%s | %s\n"
            "Error: %s\n", method.upper(), url, error)
