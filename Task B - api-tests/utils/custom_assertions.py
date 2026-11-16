def assert_status_code(response, expected_code: int | tuple[int, ...]):
    expected_codes = (expected_code,) if isinstance(expected_code, int) else expected_code
    assert response.status_code in expected_codes, f"Expected {expected_code}, but got {response.status_code}"


def response_data(response, expected_code=200):
    assert_status_code(response, expected_code)
    return response.json()


def assert_api_error(
        response,
        *,
        status_code: int | tuple[int, ...],
        code: str,
        message: str,
        fields: list[str] | None = None,
):
    assert_status_code(response, status_code)
    error = response.json().get("error")
    assert isinstance(error, dict), "Expected an 'error' object in the response"
    assert error.get("code") == code, f"Expected error code {code!r}, got {error.get('code')!r}"
    assert error.get("message") == message, (
        f"Expected error message {message!r}, got {error.get('message')!r}"
    )
    if fields is not None:
        assert error.get("fields") == fields, (
            f"Expected field errors {fields!r}, got {error.get('fields')!r}"
        )


def validate_schema(items: dict, required_keys: list):
    for key in required_keys:
        assert key in items, f"Missing key '{key}'"
        assert items[key] is not None, f"Value for key '{key}' is None"
