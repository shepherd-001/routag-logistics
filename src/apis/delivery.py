from api_client import ApiClient


class DeliveriesApiClient(ApiClient):
    def get_delivery_quote(self, payload, auth_token):
        return self.post("/deliveries/quote", json=payload, auth_token=auth_token)

    def create_draft_delivery(self, payload, auth_token):
        return self.post("/deliveries", json=payload, auth_token=auth_token)

    def get_delivery(self, delivery_id, auth_token):
        return self.get(f"/deliveries/{delivery_id}", auth_token=auth_token)

    def get_delivery_code(self, delivery_id, auth_token):
        return self.get(f"/deliveries/{delivery_id}/code", auth_token=auth_token)

    def track_delivery(self, delivery_id, auth_token):
        return self.get(f"/deliveries/{delivery_id}/tracking", auth_token=auth_token)

    def publish_draft_delivery(self, delivery_id, auth_token):
        return self.post(f"/deliveries/{delivery_id}/publish", auth_token=auth_token)

    def cancel_delivery(self, delivery_id, auth_token):
        return self.post(f"/deliveries/{delivery_id}/cancel", auth_token=auth_token)


delivery_api = DeliveriesApiClient()
