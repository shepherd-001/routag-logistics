from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from apis.auth import auth_api
from apis.courier import CourierApiClient, courier_api
from apis.delivery import delivery_api
from apis.wallet import wallet_api
from apis.webhooks import webhook_api
from utils.constant_data import DeliveryStage
from utils.custom_assertions import assert_status_code
from utils.data_factory.delivery_data_factory import DeliveryDataFactory
from utils.test_utils import TestUtils


def ledger(delivery_id, token):
    data_response = wallet_api.get_wallet_transactions(token)
    assert_status_code(data_response, 200)
    data = data_response.json()
    return sorted(
        (entry["type"], entry["amount"])
        for entry in data["data"]
        if entry["reference"] == delivery_id
    )


def delivery_code(delivery_id, token):
    code_response = delivery_api.get_delivery_code(delivery_id, token)
    assert_status_code(code_response, 200)
    return code_response.json()["code"]


@pytest.mark.parametrize("weight", [0.1, 1, 50])
def test_delivery_quote_is_created_successfully(business1_token, weight):
    payload = DeliveryDataFactory.generate_delivery_quote({"package": {"weight_kg": weight}})
    response = delivery_api.get_delivery_quote(payload, business1_token)

    assert_status_code(response, 201)
    quote = response.json()
    assert quote["quote_id"]
    assert quote["fee"] == pytest.approx(TestUtils.calculate_delivery_fee(weight))
    assert quote["currency"] == "NGN"
    assert quote["expires_at"]


@pytest.mark.parametrize("overrides, error", [
    ([{"package": {"weight_kg": 0.099}}, "package.weight_kg must be between 0.1 and 50"]),
    ([{"package": {"weight_kg": 50.001}}, "package.weight_kg must be between 0.1 and 50"]),
    ([{"package": {"weight_kg": "heavy"}}, "package.weight_kg must be between 0.1 and 50"]),
    ([{"pickup": None}, "pickup is required"]),
    ([{"dropoff": {"address": ""}}, "dropoff.address is required (5 to 200 characters)"]),
], ids=["underweight", "overweight", "text-weight", "missing-pickup", "blank-dropoff"])
def test_invalid_quote_is_rejected(business1_token, overrides, error):
    payload = DeliveryDataFactory.generate_delivery_quote(overrides)
    response = delivery_api.get_delivery_quote(payload, business1_token)

    assert_status_code(response, 422)
    response_error = response.json()["error"]
    assert response_error["code"] == "validation_error"
    assert response_error["message"] == "Invalid request"
    assert response_error["fields"] == [error]


def test_delivery_journey_settles_fee_and_updates_tracking(delivery, wallet, business1_token, courier1_token):
    opening = wallet(business1_token)
    draft = delivery(business1_token, {"package": {"weight_kg": 1}})
    delivery_id, fee = draft.id, draft.fee
    assert delivery_id and draft.status == DeliveryStage.DRAFT
    assert draft.courier_id is None
    assert draft.package.weight_kg == 1
    assert fee == TestUtils.calculate_delivery_fee(1)
    before_publish_response = courier_api.list_deliveries(courier1_token)
    assert_status_code(before_publish_response, 200)
    before_publish = before_publish_response.json()["data"]
    assert not any(row["id"] == delivery_id for row in before_publish)
    assert wallet(business1_token) == opening

    published_response = delivery_api.publish_draft_delivery(delivery_id, business1_token)
    assert_status_code(published_response, 200)
    published = published_response.json()
    assert published["status"] == DeliveryStage.PENDING
    marketplace_response = courier_api.list_deliveries(courier1_token)
    assert_status_code(marketplace_response, 200)
    marketplace = marketplace_response.json()["data"]
    assert [row["status"] for row in marketplace if row["id"] == delivery_id] == [DeliveryStage.PENDING]
    assert wallet(business1_token) == opening
    assert not ledger(delivery_id, business1_token)

    assigned_response = courier_api.accept_delivery(delivery_id, courier1_token)
    assert_status_code(assigned_response, 200)
    assigned = assigned_response.json()
    courier_response = auth_api.get_user_details(courier1_token)
    assert_status_code(courier_response, 200)
    courier = courier_response.json()
    assert (assigned["status"], assigned["courier_id"]) == (DeliveryStage.ASSIGNED, courier["id"])
    held_wallet = wallet(business1_token)
    assert held_wallet.balance == pytest.approx(opening.balance - fee)
    assert held_wallet.held == pytest.approx(opening.held + fee)
    assert ledger(delivery_id, business1_token) == [("hold", fee)]

    picked_up_response = courier_api.pickup_delivery(delivery_id, courier1_token)
    assert_status_code(picked_up_response, 200)
    picked_up = picked_up_response.json()
    assert picked_up["status"] == DeliveryStage.PICKED_UP
    assert wallet(business1_token) == held_wallet
    assert ledger(delivery_id, business1_token) == [("hold", fee)]
    assert not ledger(delivery_id, courier1_token)

    code = delivery_code(delivery_id, business1_token)
    completed_response = courier_api.deliver_delivery(delivery_id, courier1_token, code=code)
    assert_status_code(completed_response, 200)
    completed = completed_response.json()
    assert completed["status"] == DeliveryStage.DELIVERED
    settled_wallet = wallet(business1_token)
    assert settled_wallet.balance == held_wallet.balance
    assert settled_wallet.held == pytest.approx(opening.held)
    assert ledger(delivery_id, business1_token) == [("charge", fee), ("hold", fee)]
    assert ledger(delivery_id, courier1_token) == [("payout", TestUtils.calculate_courier_fee(fee))]
    tracking_response = delivery_api.track_delivery(delivery_id, business1_token)
    assert_status_code(tracking_response, 200)
    tracking = tracking_response.json()
    assert tracking["status"] == DeliveryStage.DELIVERED
    assert [entry["status"] for entry in tracking["history"]] == [
        DeliveryStage.DRAFT, DeliveryStage.PENDING, DeliveryStage.ASSIGNED, DeliveryStage.PICKED_UP,
        DeliveryStage.DELIVERED,
    ]


@pytest.mark.parametrize("stage",
                         [DeliveryStage.DRAFT, DeliveryStage.PENDING, DeliveryStage.ASSIGNED, DeliveryStage.PICKED_UP])
def test_business_can_cancel_before_completion(staged_delivery, wallet, business1_token, courier1_token, stage):
    opening = wallet(business1_token)
    draft = staged_delivery(stage)
    cancelled_response = delivery_api.cancel_delivery(draft.id, business1_token)
    assert_status_code(cancelled_response, 200)
    cancelled = cancelled_response.json()
    assert cancelled["status"] == DeliveryStage.CANCELLED
    restored = wallet(business1_token)
    assert restored.balance == pytest.approx(opening.balance)
    assert restored.held == pytest.approx(opening.held)
    expected = [("hold", draft.fee)] if stage in {DeliveryStage.ASSIGNED, DeliveryStage.PICKED_UP} else []
    assert ledger(draft.id, business1_token) == expected
    assert not ledger(draft.id, courier1_token)
    accept_response = courier_api.accept_delivery(draft.id, courier1_token)
    assert_status_code(accept_response, (403, 404, 409))


@pytest.mark.parametrize("attempt", ["before_pickup", "wrong", "blank", "oversized"])
def test_invalid_completion_preserves_the_hold(staged_delivery, wallet, business1_token, courier1_token, attempt):
    stage = DeliveryStage.ASSIGNED if attempt == "before_pickup" else DeliveryStage.PICKED_UP
    draft = staged_delivery(stage)
    valid = delivery_code(draft.id, business1_token)
    wrong = ("1" if valid[0] != "1" else "2") + valid[1:]
    code = {"before_pickup": valid, "wrong": wrong, "blank": "", "oversized": valid * 64}[attempt]
    before = wallet(business1_token)

    response = courier_api.deliver_delivery(draft.id, courier1_token, code=code)

    assert_status_code(response, (400, 409, 422))
    delivery_response = delivery_api.get_delivery(draft.id, business1_token)
    assert_status_code(delivery_response, 200)
    assert delivery_response.json()["status"] == stage
    assert wallet(business1_token) == before
    assert ledger(draft.id, business1_token) == [("hold", draft.fee)]
    assert not ledger(draft.id, courier1_token)


def test_acceptance_retry_creates_only_one_hold(staged_delivery, wallet, business1_token, courier1_token):
    draft = staged_delivery(DeliveryStage.ASSIGNED)
    held = wallet(business1_token)
    retry = courier_api.accept_delivery(draft.id, courier1_token)
    assert_status_code(retry, (200, 409))
    assert ledger(draft.id, business1_token) == [("hold", draft.fee)]
    assert wallet(business1_token) == held


@pytest.mark.parametrize("action", ["retry_delivery", "cancel"])
def test_completed_delivery_settlement_is_final(staged_delivery, wallet, business1_token, courier1_token, action):
    draft = staged_delivery(DeliveryStage.PICKED_UP)
    code = delivery_code(draft.id, business1_token)
    completion_response = courier_api.deliver_delivery(draft.id, courier1_token, code=code)
    assert_status_code(completion_response, 200)
    settled_wallet = wallet(business1_token)
    business_entries = ledger(draft.id, business1_token)
    courier_entries = ledger(draft.id, courier1_token)
    assert business_entries == [("charge", draft.fee), ("hold", draft.fee)]
    assert courier_entries == [("payout", TestUtils.calculate_courier_fee(draft.fee))]

    if action == "retry_delivery":
        response = courier_api.deliver_delivery(draft.id, courier1_token, code=code)
        assert_status_code(response, (200, 409))
    else:
        response = delivery_api.cancel_delivery(draft.id, business1_token)
        assert_status_code(response, (403, 409))
    delivery_response = delivery_api.get_delivery(draft.id, business1_token)
    assert_status_code(delivery_response, 200)
    assert delivery_response.json()["status"] == DeliveryStage.DELIVERED
    assert ledger(draft.id, business1_token) == business_entries
    assert ledger(draft.id, courier1_token) == courier_entries
    assert wallet(business1_token) == settled_wallet


@pytest.mark.parametrize("action, stage", [
    ("get_delivery", DeliveryStage.ASSIGNED),
    ("get_delivery_code", DeliveryStage.ASSIGNED),
    ("track_delivery", DeliveryStage.ASSIGNED),
    ("publish_draft_delivery", DeliveryStage.DRAFT),
    ("cancel_delivery", DeliveryStage.ASSIGNED),
])
def test_other_business_cannot_access_delivery(staged_delivery, wallet, business1_token, business2_token, action,
                                               stage):
    draft = staged_delivery(stage)
    second_business_response = auth_api.get_user_details(business2_token)
    assert_status_code(second_business_response, 200)
    second_business = second_business_response.json()
    assert second_business["id"] != draft.business_id
    before = wallet(business1_token), ledger(draft.id, business1_token)

    response = getattr(delivery_api, action)(draft.id, business2_token)

    assert_status_code(response, (403, 404))
    delivery_response = delivery_api.get_delivery(draft.id, business1_token)
    assert_status_code(delivery_response, 200)
    assert delivery_response.json()["status"] == stage
    assert (wallet(business1_token), ledger(draft.id, business1_token)) == before


@pytest.mark.parametrize("action", ["accept_delivery", "pickup_delivery", "deliver_delivery", "cancel_delivery"])
def test_other_courier_cannot_take_over_delivery(staged_delivery, wallet, business1_token, courier2_token, action):
    stage = DeliveryStage.PICKED_UP if action == "deliver_delivery" else DeliveryStage.ASSIGNED
    draft = staged_delivery(stage)
    assigned_response = delivery_api.get_delivery(draft.id, business1_token)
    assert_status_code(assigned_response, 200)
    assigned = assigned_response.json()
    other_courier_response = auth_api.get_user_details(courier2_token)
    assert_status_code(other_courier_response, 200)
    other_courier = other_courier_response.json()
    assert other_courier["id"] != assigned["courier_id"]
    before = wallet(business1_token), ledger(draft.id, business1_token)
    kwargs = {"code": delivery_code(draft.id, business1_token)} if stage == DeliveryStage.PICKED_UP else {}

    response = getattr(courier_api, action)(draft.id, courier2_token, **kwargs)

    assert_status_code(response, (403, 404, 409))
    after_response = delivery_api.get_delivery(draft.id, business1_token)
    assert_status_code(after_response, 200)
    after = after_response.json()
    assert (after["status"], after["courier_id"]) == (stage, assigned["courier_id"])
    assert (wallet(business1_token), ledger(draft.id, business1_token)) == before
    assert not ledger(draft.id, courier2_token)


def test_only_one_courier_can_accept_concurrently(staged_delivery, business1_token, courier1_token, courier2_token):
    draft = staged_delivery(DeliveryStage.PENDING)
    tokens = (courier1_token, courier2_token)
    courier_ids = []
    for token in tokens:
        profile_response = auth_api.get_user_details(token)
        assert_status_code(profile_response, 200)
        courier_ids.append(profile_response.json()["id"])
    assert courier_ids[0] != courier_ids[1]
    ready = Barrier(2, timeout=5)

    def accept(token):
        client = CourierApiClient()
        try:
            ready.wait()
            return client.accept_delivery(draft.id, token).status_code
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=2) as workers:
        statuses = list(workers.map(accept, tokens))

    assert statuses.count(200) == 1, f"Concurrent acceptance returned {statuses}"
    assert next(status for status in statuses if status != 200) in {403, 404, 409}
    assigned_response = delivery_api.get_delivery(draft.id, business1_token)
    assert_status_code(assigned_response, 200)
    assigned = assigned_response.json()
    assert (assigned["status"], assigned["courier_id"]) == (DeliveryStage.ASSIGNED, courier_ids[statuses.index(200)])
    assert ledger(draft.id, business1_token) == [("hold", draft.fee)]


def test_completion_logs_one_webhook_event(staged_delivery, business1_token, courier1_token):
    draft = staged_delivery(DeliveryStage.PICKED_UP)
    code = delivery_code(draft.id, business1_token)
    completion_response = courier_api.deliver_delivery(draft.id, courier1_token, code=code)
    assert_status_code(completion_response, 200)

    events_response = webhook_api.list_webhook_events(business1_token)
    assert_status_code(events_response, 200)
    events = events_response.json()["data"]
    completed = [event for event in events if
                 event["delivery_id"] == draft.id and event["type"] == "delivery.delivered"]
    assert len(completed) == 1
    assert completed[0]["status"] == DeliveryStage.DELIVERED
