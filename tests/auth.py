from apis.auth import auth_api
from config import settings
from utils.custom_assertions import assert_status_code

email = settings.business_email
password = settings.business_password


def test_some():
    response = auth_api.login(email, password)

    assert_status_code(response, 200)
    data = response.json()
    assert data["token"] is not None
    assert data["user"]["id"] == "biz_1"
    assert data["user"]["name"] == "Ade Stores"
    assert data["user"]["role"] == "business"
