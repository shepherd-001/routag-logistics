from api_client import ApiClient


class SandboxApiClient(ApiClient):
    def rest_sandbox_data(self):
        return self.post("/reset")


sandbox_api = SandboxApiClient()
