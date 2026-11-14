def assert_status_code(response, expected_code):
    assert response.status_code == expected_code, f"Expected {expected_code}, but got {response.status_code}"


def validate_schema(items: dict, required_keys: list):
    for key in required_keys:
        assert key in items, f"Missing key '{key}'"
        assert items[key] is not None, f"Value for key '{key}' is None"
