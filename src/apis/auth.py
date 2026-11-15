from api_client import ApiClient


class AuthApiClient(ApiClient):
    def login(self, email, password):
        payload = {
            "email": email,
            "password": password,
        }
        return self.post("/auth/login", json=payload)

    def get_user_details(self, auth_token):
        return self.get("/me", auth_token=auth_token)


auth_api = AuthApiClient()
