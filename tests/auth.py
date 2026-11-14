from apis.auth import auth_api
from config import settings
from utils.custom_assertions import assert_status_code


def test_business1_can_login_successfully():
    response = auth_api.login(settings.business1_email, settings.business1_password)

    assert_status_code(response, 200)
    data = response.json()
    assert data["token"] is not None
    assert data["user"]["id"] == "biz_1"
    assert data["user"]["name"] == "Ade Stores"
    assert data["user"]["role"] == "business"


def test_business2_can_login_successfully():
    response = auth_api.login(settings.business2_email, settings.business2_password)

    assert_status_code(response, 200)
    data = response.json()
    assert data["token"] is not None
    assert data["user"]["id"] == "biz_2"
    assert data["user"]["name"] == "Lagos Pharmacy"
    assert data["user"]["role"] == "business"


def test_courier1_can_login_successfully():
    response = auth_api.login(settings.courier1_email, settings.courier1_password)

    assert_status_code(response, 200)
    data = response.json()
    assert data["token"] is not None
    assert data["user"]["id"] == "cou_1"
    assert data["user"]["name"] == "Tunde Courier"
    assert data["user"]["role"] == "courier"


def test_courier2_can_login_successfully():
    response = auth_api.login(settings.courier1_email, settings.courier1_password)

    assert_status_code(response, 200)
    data = response.json()
    assert data["token"] is not None
    assert data["user"]["id"] == "cou_1"
    assert data["user"]["name"] == "Tunde Courier"
    assert data["user"]["role"] == "courier"
