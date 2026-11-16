from api_client import ApiClient


class WebhooksApiClient(ApiClient):
    def set_webhook_url(self, url, auth_token):
        payload = {
            "url": url,
        }
        return self.put("/webhook", json=payload, auth_token=auth_token)

    def list_webhook_events(self, auth_token):
        return self.get("/webhook/events", auth_token=auth_token)


webhook_api = WebhooksApiClient()
