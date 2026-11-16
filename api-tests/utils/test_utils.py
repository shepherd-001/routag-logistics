import random
from copy import deepcopy

from config import fake


class TestUtils:
    @staticmethod
    def generate_phone_number() -> str:
        prefixes = ["070", "080", "081", "090", "091"]
        prefix = random.choice(prefixes)
        number = fake.numerify("########")

        return f"{prefix}{number}"

    @staticmethod
    def calculate_delivery_fee(weight_kg: int | float) -> int | float:
        return 1500 + 200 * weight_kg

    @staticmethod
    def calculate_courier_fee(delivery_fee: int | float) -> int | float:
        return delivery_fee * 0.8

    @staticmethod
    def deep_merge(base: dict, overrides: dict) -> dict:
        """Recursively merge overrides into base dict without mutating the original."""
        result = deepcopy(base)
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = TestUtils.deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result
