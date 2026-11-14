from api_client import ApiClient


class CourierApiClient(ApiClient):
    def list_deliveries(self, auth_token):
        return self.get("/courier/deliveries", auth_token=auth_token)

    def accept_delivery(self, delivery_id, auth_token):
        return self.post(f"/courier/deliveries/{delivery_id}/accept", auth_token=auth_token)

    def pickup_delivery(self, delivery_id, auth_token):
        return self.post(f"/courier/deliveries/{delivery_id}/pickup", auth_token=auth_token)

    def deliver_delivery(self, delivery_id, auth_token):
        return self.post(f"/courier/deliveries/{delivery_id}/deliver", auth_token=auth_token)

    def cancel_delivery(self, delivery_id, auth_token):
        return self.post(f"/courier/deliveries/{delivery_id}/cancel", auth_token=auth_token)


courier_api = CourierApiClient()
