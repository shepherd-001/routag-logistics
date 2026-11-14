import pytest

from apis.auth import auth_api
from apis.courier import courier_api
from apis.delivery import delivery_api
from apis.wallet import wallet_api
from config import settings
from utils.constant_data import DeliveryStage
from utils.data_factory.delivery_data_factory import DeliveryDataFactory
from utils.fixture_models import (
    DeliveryContact, DeliveryHistoryEntry, DeliveryInfo, DeliveryPackage, DeliveryQuoteInfo, WalletInfo,
)


def user_details(email: str, password: str):
    response = auth_api.login(email, password)
    assert response.status_code == 200, "Failed to login"
    return response.json()


@pytest.fixture(scope="session")
def user_token():
    def _get_token(email: str, password: str):
        login_response = user_details(email, password)
        return login_response["token"]

    return _get_token


@pytest.fixture(scope="session")
def business1_token(user_token):
    return user_token(settings.business1_email, settings.business1_password)


@pytest.fixture(scope="session")
def courier1_token(user_token):
    return user_token(settings.courier1_email, settings.courier1_password)


@pytest.fixture(scope="session")
def business2_token(user_token):
    return user_token(settings.business2_email, settings.business2_password)


@pytest.fixture(scope="session")
def courier2_token(user_token):
    return user_token(settings.courier2_email, settings.courier2_password)


@pytest.fixture
def delivery_quote():
    def _create_delivery_quote(auth_token: str, overrides=None):
        payload = DeliveryDataFactory.generate_delivery_quote(overrides)
        response = delivery_api.get_delivery_quote(payload, auth_token)

        assert response.status_code == 201, "Failed to get delivery quote"
        data = response.json()
        return DeliveryQuoteInfo(id=data["quote_id"], fee=data["fee"], currency=data["currency"],
                                 expires_at=data["expires_at"])

    return _create_delivery_quote


@pytest.fixture
def wallet():
    def _resolve_wallet_details(token: str):
        response = wallet_api.get_wallet_details(token)
        assert response.status_code == 200, "Failed to get wallet details"

        data = response.json()
        return WalletInfo(balance=data["balance"], held=data["held"])

    return _resolve_wallet_details


@pytest.fixture
def delivery():
    def _create_delivery(auth_token: str, overrides=None):
        delivery_quote_payload = DeliveryDataFactory.generate_delivery_quote(overrides)
        delivery_quote_response = delivery_api.get_delivery_quote(delivery_quote_payload, auth_token)

        assert delivery_quote_response.status_code == 201, "Failed to get delivery quote"
        delivery_quote = delivery_quote_response.json()

        delivery_quote_payload["quote_id"] = delivery_quote["quote_id"]
        delivery_response = delivery_api.create_draft_delivery(delivery_quote_payload, auth_token)

        assert delivery_response.status_code == 201, "Failed to create draft delivery"
        data = delivery_response.json()

        return DeliveryInfo(id=data["id"], business_id=data["business_id"], status=data["status"], fee=data["fee"],
                            currency=data["currency"], pickup=DeliveryContact(**data["pickup"]),
                            drop_off=DeliveryContact(**data["dropoff"]), package=DeliveryPackage(**data["package"]),
                            courier_id=data["courier_id"],
                            history=tuple(DeliveryHistoryEntry(**entry) for entry in data["history"]))

    return _create_delivery


@pytest.fixture
def staged_delivery(delivery, business1_token, courier1_token):
    def create(stage):
        draft = delivery(business1_token, {"package": {"weight_kg": 1}})
        transitions = (
            (DeliveryStage.PENDING, delivery_api.publish_draft_delivery, business1_token),
            (DeliveryStage.ASSIGNED, courier_api.accept_delivery, courier1_token),
            (DeliveryStage.PICKED_UP, courier_api.pickup_delivery, courier1_token),
        )
        if stage == DeliveryStage.DRAFT:
            return draft
        print(transitions)
        for status, transition, token in transitions:
            response = transition(draft.id, token)
            assert response.status_code == 200, f"Setup for {status} returned HTTP {response.status_code}"
            assert response.json()["status"] == status
            if stage == status:
                return draft
        raise ValueError(f"Unknown delivery stage: {stage}")

    return create
