import pytest

from apis.auth import auth_api
from apis.courier import courier_api
from apis.delivery import delivery_api
from apis.wallet import wallet_api
from config import settings
from utils.constant_data import DeliveryStage
from utils.custom_assertions import response_data
from utils.data_factory.delivery_data_factory import DeliveryDataFactory
from utils.fixture_models import (
    DeliveryContact, DeliveryHistoryEntry, DeliveryInfo, DeliveryPackage, WalletInfo,
)


@pytest.fixture(scope="session")
def user_details():
    def get_details(token):
        response = auth_api.get_user_details(token)
        return response_data(response, 200)

    return get_details


@pytest.fixture(scope="session")
def login_token():
    def _get_token(email: str, password: str):
        response = auth_api.login(email, password)
        login_response = response_data(response, 200)
        return login_response["token"]

    return _get_token


@pytest.fixture(scope="session")
def business1_token(login_token):
    return login_token(settings.business1_email, settings.business1_password)


@pytest.fixture(scope="session")
def courier1_token(login_token):
    return login_token(settings.courier1_email, settings.courier1_password)


@pytest.fixture(scope="session")
def business2_token(login_token):
    return login_token(settings.business2_email, settings.business2_password)


@pytest.fixture(scope="session")
def courier2_token(login_token):
    return login_token(settings.courier2_email, settings.courier2_password)


@pytest.fixture
def wallet():
    def _resolve_wallet_details(token: str):
        response = wallet_api.get_wallet_details(token)

        wallet_data = response_data(response, 200)
        return WalletInfo(balance=wallet_data["balance"], held=wallet_data["held"])

    return _resolve_wallet_details


def _delivery_info(data):
    return DeliveryInfo(
        id=data["id"],
        business_id=data["business_id"],
        status=data["status"],
        fee=data["fee"],
        currency=data["currency"],
        pickup=DeliveryContact(**data["pickup"]),
        drop_off=DeliveryContact(**data["dropoff"]),
        package=DeliveryPackage(**data["package"]),
        courier_id=data["courier_id"],
        history=tuple(DeliveryHistoryEntry(**entry) for entry in data["history"]),
    )


@pytest.fixture
def delivery():
    def _create_delivery(auth_token: str, overrides=None):
        delivery_quote_payload = DeliveryDataFactory.generate_delivery_quote(overrides)
        delivery_quote_response = delivery_api.get_delivery_quote(delivery_quote_payload, auth_token)
        delivery_quote = response_data(delivery_quote_response, 201)

        delivery_quote_payload["quote_id"] = delivery_quote["quote_id"]
        delivery_response = delivery_api.create_draft_delivery(delivery_quote_payload, auth_token)

        delivery_data = response_data(delivery_response, 201)
        return _delivery_info(delivery_data)

    return _create_delivery


@pytest.fixture
def staged_delivery(delivery, business1_token, courier1_token):
    transitions = (
        (DeliveryStage.PENDING, delivery_api.publish_draft_delivery, business1_token),
        (DeliveryStage.ASSIGNED, courier_api.accept_delivery, courier1_token),
        (DeliveryStage.PICKED_UP, courier_api.pickup_delivery, courier1_token),
    )

    def _advance_to(stage):
        if stage != DeliveryStage.DRAFT and stage not in [status for status, _, _ in transitions]:
            raise ValueError(f"Unknown delivery stage: {stage}")

        # draft = delivery(business1_token, {"package": {"weight_kg": 1}})
        current = delivery(business1_token)
        if stage == DeliveryStage.DRAFT:
            return current
        for status, transition, token in transitions:
            response = transition(current.id, token)
            data = response_data(response, 200)
            assert data["status"] == status
            if stage == status:
                return _delivery_info(data)

        return current

    return _advance_to
