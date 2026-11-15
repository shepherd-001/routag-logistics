from api_client import ApiClient


class ApiKeysApiClient(ApiClient):
    def create_api_key(self, auth_token):
        return self.post("/api-keys", auth_token=auth_token)

    def list_api_keys(self, auth_token):
        return self.get("/api-keys", auth_token=auth_token)

    def revoke_api_key(self, api_key_id, auth_token):
        return self.delete(f"/api-keys/{api_key_id}", auth_token=auth_token)


api_keys_api = ApiKeysApiClient()
