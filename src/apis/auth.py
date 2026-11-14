from api_client import ApiClient


class AuthAPIClient(ApiClient):
    def login(self, email, password):
        payload = {
            "email": email,
            "password": password,
        }
        return self.post("/auth/login", json=payload)


auth_api = AuthAPIClient()
