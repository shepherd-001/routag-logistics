from apis.delivery import delivery_api
from config import settings
from utils.data_factory.delivery_data_factory import DeliveryDataFactory
from utils.test_utils import TestUtils


class TestDeliveryJourney:

    def test_delivery_quote_is_created_successfully(self, business1_token):
        payload = DeliveryDataFactory.generate_delivery_quote()
        response = delivery_api.get_delivery_quote(payload, business1_token)
        assert response.status_code == 201
        quote = response.json()
        assert quote["quote_id"] is not None
        assert quote["fee"] == TestUtils.calculate_delivery_fee(payload["package"]["weight_kg"])
        assert quote["currency"] == "NGN"
        assert quote["expires_at"] is not None

    def test_som(self, delivery, business1_token):
        print(delivery(business1_token))
