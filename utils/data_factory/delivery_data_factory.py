from config import fake
from utils.test_utils import TestUtils


class DeliveryDataFactory:
    @staticmethod
    def generate_delivery_quote(overrides=None, quote_id=None):
        delivery_data = {
            "pickup": {
                "name": fake.name(),
                "phone": TestUtils.generate_phone_number(),
                "address": fake.address()
            },
            "dropoff": {
                "name": fake.name(),
                "phone": TestUtils.generate_phone_number(),
                "address": fake.address()
            },
            "package": {
                "description": TestUtils.generate_text(200),
                "weight_kg": fake.random_int(min=10, max=500) / 100,
            },
        }

        if quote_id is not None:
            delivery_data["quote_id"] = quote_id

        if overrides:
            return TestUtils.deep_merge(delivery_data, overrides)
        return delivery_data
