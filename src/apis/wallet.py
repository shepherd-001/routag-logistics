from api_client import ApiClient


class WalletApiClient(ApiClient):
    def top_up_wallet(self, auth_token):
        return self.post("/wallet/top-up", auth_token=auth_token)

    def get_wallet_details(self, auth_token):
        return self.get("/wallet", auth_token=auth_token)

    def get_wallet_transactions(self, auth_token):
        return self.get("/transactions", auth_token=auth_token)


wallet_api = WalletApiClient()
