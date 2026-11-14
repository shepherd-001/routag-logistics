def assert_status_code(response, expected_code: int | tuple[int, ...]):
    expected_codes = (expected_code,) if isinstance(expected_code, int) else expected_code
    assert response.status_code in expected_codes, f"Expected {expected_code}, but got {response.status_code}"


def response_data(response, expected=200):
    assert_status_code(response, expected)
    return response.json()


def validate_schema(items: dict, required_keys: list):
    for key in required_keys:
        assert key in items, f"Missing key '{key}'"
        assert items[key] is not None, f"Value for key '{key}' is None"
