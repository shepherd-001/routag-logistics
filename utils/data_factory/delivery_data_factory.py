from config import fake
from utils.test_utils import TestUtils


class DeliveryDataFactory:
    @staticmethod
    def generate_delivery__quote_data(overrides=None):
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
                "description": fake.sentence(nb_words=5),
                "weight_kg": fake.pydecimal(right_digits=2, min_value=0, max_value=500 ),
            }
        }

        if overrides:
            return TestUtils.deep_merge(delivery_data, overrides)
        return delivery_data
