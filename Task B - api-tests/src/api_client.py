import requests

from config import settings
from config.logger import ApiLogger


class ApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10):
        self.base_url = (base_url or "").rstrip("/") or settings.base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = ApiLogger()

    def request(self, method: str, path: str, auth_token: str | None = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = dict(kwargs.pop("headers", None) or {})

        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        body = kwargs.get("json", kwargs.get("data"))

        self.logger.log_request(method, url, headers, body)

        try:
            response = self.session.request(method, url, headers=headers, timeout=kwargs.pop("timeout", self.timeout),
                                            **kwargs, )

            try:
                response_body = response.json()
            except ValueError:
                response_body = response.text

            self.logger.log_response(
                response.status_code,
                response.url,
                dict(response.headers),
                response_body,
            )

            return response

        except requests.RequestException as error:
            self.logger.log_error(method, url, error)
            raise

    def get(self, path: str, auth_token: str | None = None, **kwargs) -> requests.Response:
        return self.request("GET", path, auth_token=auth_token, **kwargs)

    def post(self, path: str, auth_token: str | None = None, **kwargs) -> requests.Response:
        return self.request("POST", path, auth_token=auth_token, **kwargs)

    def put(self, path: str, auth_token: str | None = None, **kwargs) -> requests.Response:
        return self.request("PUT", path, auth_token=auth_token, **kwargs)

    def patch(self, path: str, auth_token: str | None = None, **kwargs) -> requests.Response:
        return self.request("PATCH", path, auth_token=auth_token, **kwargs)

    def delete(self, path: str, auth_token: str | None = None, **kwargs) -> requests.Response:
        return self.request("DELETE", path, auth_token=auth_token, **kwargs)

    def close(self) -> None:
        self.session.close()
