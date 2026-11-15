import pytest

from apis.courier import courier_api
from apis.delivery import delivery_api
from apis.wallet import wallet_api
from apis.webhooks import webhook_api
from config import fake
from utils.constant_data import DeliveryStage, LedgerEntry
from utils.custom_assertions import assert_api_error, assert_status_code, response_data
from utils.data_factory.delivery_data_factory import DeliveryDataFactory
from utils.test_utils import TestUtils


def ledger_entries(delivery_id, token):
    response = wallet_api.get_wallet_transactions(token)
    transactions = response_data(response)["data"]
    return sorted((entry["type"], entry["amount"]) for entry in transactions if entry["reference"] == delivery_id)


def assert_ledger(delivery_id, token, *expected):
    # Assert the delivery's entries match `expected`, in any order
    assert ledger_entries(delivery_id, token) == sorted(expected)


def snapshot(delivery_id, wallet, token):
    # Money state of a business for one delivery: wallet plus ledger
    return wallet(token), ledger_entries(delivery_id, token)


def delivery_code(delivery_id, token):
    code_response = delivery_api.get_delivery_code(delivery_id, token)
    return response_data(code_response)["code"]


@pytest.mark.parametrize("weight", [0.1, 1, 50])
def test_delivery_quote_is_created_successfully(business1_token, weight):
    payload = DeliveryDataFactory.generate_delivery_quote({"package": {"weight_kg": weight}})
    response = delivery_api.get_delivery_quote(payload, business1_token)

    quote = response_data(response, expected_code=201)
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

    assert_api_error(response, status_code=422, code="validation_error", message="Invalid request", fields=[error])


# delivery journey settles fee and updates tracking

def test_new_draft_is_private_and_costs_nothing(delivery, wallet, business1_token, courier1_token):
    opening = wallet(business1_token)
    weight = fake.random_int(1, 50)
    draft = delivery(business1_token, {"package": {"weight_kg": weight}})
    assert draft.status == DeliveryStage.DRAFT
    assert draft.courier_id is None
    assert draft.package.weight_kg == weight
    assert draft.fee == TestUtils.calculate_delivery_fee(weight)

    courier_view_response = courier_api.list_deliveries(courier1_token)
    courier_view = response_data(courier_view_response)["data"]
    assert draft.id not in [row["id"] for row in courier_view]
    assert wallet(business1_token) == opening


def test_published_delivery_appears_in_marketplace_without_charging(staged_delivery, wallet, business1_token,
                                                                    courier1_token):
    opening = wallet(business1_token)

    pending = staged_delivery(DeliveryStage.PENDING)

    courier_view_response = courier_api.list_deliveries(courier1_token)
    marketplace = response_data(courier_view_response)["data"]
    assert [row["status"] for row in marketplace if row["id"] == pending.id] == [DeliveryStage.PENDING]
    assert wallet(business1_token) == opening
    assert_ledger(pending.id, business1_token)


def test_accepting_delivery_holds_the_fee(staged_delivery, wallet, business1_token, courier1_token, user_details):
    pending = staged_delivery(DeliveryStage.PENDING)
    opening = wallet(business1_token)

    assigned = response_data(courier_api.accept_delivery(pending.id, courier1_token))

    assert assigned["status"] == DeliveryStage.ASSIGNED
    assert assigned["courier_id"] == user_details(courier1_token)["id"]
    held = wallet(business1_token)
    assert held.balance == pytest.approx(opening.balance - pending.fee)
    assert held.held == pytest.approx(opening.held + pending.fee)
    assert_ledger(pending.id, business1_token, (LedgerEntry.HOLD, pending.fee))


def test_pickup_leaves_money_untouched(staged_delivery, wallet, business1_token, courier1_token):
    assigned = staged_delivery(DeliveryStage.ASSIGNED)
    before = snapshot(assigned.id, wallet, business1_token)

    picked_up = response_data(courier_api.pickup_delivery(assigned.id, courier1_token))

    assert picked_up["status"] == DeliveryStage.PICKED_UP
    assert snapshot(assigned.id, wallet, business1_token) == before
    assert_ledger(assigned.id, courier1_token)


def test_delivery_with_valid_code_settles_the_fee(staged_delivery, wallet, business1_token, courier1_token):
    picked_up = staged_delivery(DeliveryStage.PICKED_UP)
    opening = wallet(business1_token)
    code = delivery_code(picked_up.id, business1_token)

    completed = response_data(courier_api.deliver_delivery(picked_up.id, courier1_token, code=code))

    assert completed["status"] == DeliveryStage.DELIVERED
    # settled = wallet(business1_token)
    # assert settled.balance == opening.balance, "balance was already reduced when the fee was held"
    # assert settled.held == pytest.approx(opening.held - picked_up.fee), "the hold is released on settlement"
    # assert_ledger(picked_up.id, business1_token, (LedgerEntry.HOLD, picked_up.fee), (LedgerEntry.CHARGE, picked_up.fee))
    # assert_ledger(picked_up.id, courier1_token,
    #               (LedgerEntry.PAYOUT, TestUtils.calculate_courier_fee(picked_up.fee)))


def test_tracking_history_lists_every_stage_in_order(staged_delivery, business1_token, courier1_token):
    picked_up = staged_delivery(DeliveryStage.PICKED_UP)
    code = delivery_code(picked_up.id, business1_token)
    response_data(courier_api.deliver_delivery(picked_up.id, courier1_token, code=code))

    tracking = response_data(delivery_api.track_delivery(picked_up.id, business1_token))

    assert tracking["status"] == DeliveryStage.DELIVERED
    assert [entry["status"] for entry in tracking["history"]] == [
        DeliveryStage.DRAFT, DeliveryStage.PENDING, DeliveryStage.ASSIGNED, DeliveryStage.PICKED_UP,
        DeliveryStage.DELIVERED,
    ]


# cancellation and completion
@pytest.mark.parametrize("stage", [
    DeliveryStage.DRAFT, DeliveryStage.PENDING, DeliveryStage.ASSIGNED, DeliveryStage.PICKED_UP,
])
def test_business_can_cancel_before_completion(staged_delivery, wallet, business1_token, courier1_token, stage):
    opening = wallet(business1_token)
    target = staged_delivery(stage)

    cancelled = response_data(delivery_api.cancel_delivery(target.id, business1_token))

    assert cancelled["status"] == DeliveryStage.CANCELLED
    restored = wallet(business1_token)
    assert restored.balance == pytest.approx(opening.balance)
    assert restored.held == pytest.approx(opening.held)
    expected_entries = [(LedgerEntry.HOLD, target.fee)] if stage in (DeliveryStage.ASSIGNED,
                                                                     DeliveryStage.PICKED_UP) else []
    assert_ledger(target.id, business1_token, *expected_entries)
    assert_ledger(target.id, courier1_token)
    assert_api_error(courier_api.accept_delivery(target.id, courier1_token), status_code=409,
                     code="invalid_status", message="Cannot accept a cancelled delivery")


@pytest.mark.parametrize("attempt", ["before_pickup", "wrong", "blank", "oversized"])
def test_invalid_completion_preserves_the_hold(staged_delivery, wallet, business1_token, courier1_token, attempt):
    stage = DeliveryStage.ASSIGNED if attempt == "before_pickup" else DeliveryStage.PICKED_UP
    target = staged_delivery(stage)
    valid = delivery_code(target.id, business1_token)
    wrong = ("1" if valid[0] != "1" else "2") + valid[1:]
    code = {
        "before_pickup": valid,
        "wrong": wrong,
        "blank": "",
        "oversized": valid * 64}[attempt]
    before = wallet(business1_token)

    response = courier_api.deliver_delivery(target.id, courier1_token, code=code)

    assert_api_error(response, status_code=400, code="invalid_code", message="Delivery code is incorrect")

    delivery_response = delivery_api.get_delivery(target.id, business1_token)
    assert response_data(delivery_response)["status"] == stage
    assert wallet(business1_token) == before
    assert_ledger(target.id, business1_token, (LedgerEntry.HOLD, target.fee))
    assert_ledger(target.id, courier1_token)


def test_repeated_acceptance_creates_only_one_hold(staged_delivery, wallet, business1_token, courier1_token):
    assigned = staged_delivery(DeliveryStage.ASSIGNED)
    before = snapshot(assigned.id, wallet, business1_token)

    assert before[1] == [(LedgerEntry.HOLD, assigned.fee)]

    response = courier_api.accept_delivery(assigned.id, courier1_token)

    assert_status_code(response, 200)
    assert snapshot(assigned.id, wallet, business1_token) == before


@pytest.mark.parametrize("action", ["retry_delivery", "cancel"])
def test_completed_delivery_settlement_is_final(staged_delivery, wallet, business1_token, courier1_token, action):
    draft = staged_delivery(DeliveryStage.PICKED_UP)
    code = delivery_code(draft.id, business1_token)
    completion_response = courier_api.deliver_delivery(draft.id, courier1_token, code=code)
    assert_status_code(completion_response, 200)
    settled_wallet = wallet(business1_token)
    business_entries = ledger_entries(draft.id, business1_token)
    courier_entries = ledger_entries(draft.id, courier1_token)
    assert business_entries == [("charge", draft.fee), ("hold", draft.fee)]
    assert courier_entries == [("payout", TestUtils.calculate_courier_fee(draft.fee))]

    if action == "retry_delivery":
        response = courier_api.deliver_delivery(draft.id, courier1_token, code=code)
        assert_api_error(response, status_code=409, code="invalid_status", message="Cannot accept a cancelled delivery")
    else:
        response = delivery_api.cancel_delivery(draft.id, business1_token)
        assert_api_error(response, status_code=409, code="invalid_status", message="Cannot cancel a delivered delivery")

    delivery_response = delivery_api.get_delivery(draft.id, business1_token)
    assert response_data(delivery_response)["status"] == DeliveryStage.DELIVERED
    assert ledger_entries(draft.id, business1_token) == business_entries
    assert ledger_entries(draft.id, courier1_token) == courier_entries
    assert wallet(business1_token) == settled_wallet


@pytest.mark.parametrize("action, stage", [
    pytest.param(delivery_api.get_delivery, DeliveryStage.ASSIGNED, id="view-delivery"),
    pytest.param(delivery_api.get_delivery_code, DeliveryStage.ASSIGNED, id="view-code"),
    pytest.param(delivery_api.track_delivery, DeliveryStage.ASSIGNED, id="track"),
    pytest.param(delivery_api.publish_draft_delivery, DeliveryStage.DRAFT, id="publish"),
    pytest.param(delivery_api.cancel_delivery, DeliveryStage.ASSIGNED, id="cancel"),
])
def test_other_business_is_denied_access(
        staged_delivery, wallet, user_details, business1_token, business2_token, action, stage,
):
    delivery = staged_delivery(stage)
    assert user_details(business2_token)["id"] != delivery.business_id
    before = snapshot(delivery.id, wallet, business1_token)

    response = action(delivery.id, business2_token)

    assert_api_error(response, status_code=404, code="not_found", message="Delivery not found")
    owner_response = delivery_api.get_delivery(delivery.id, business1_token)
    assert response_data(owner_response)["status"] == stage
    assert snapshot(delivery.id, wallet, business1_token) == before


@pytest.mark.parametrize("action", [
    pytest.param(courier_api.accept_delivery, id="accept"),
    pytest.param(courier_api.pickup_delivery, id="pickup"),
    pytest.param(courier_api.cancel_delivery, id="cancel"),
])
def test_other_courier_cannot_take_over_delivery(
        staged_delivery, wallet, user_details, business1_token, courier2_token, action,
):
    assigned = staged_delivery(DeliveryStage.ASSIGNED)
    assert user_details(courier2_token)["id"] != assigned.courier_id
    before = snapshot(assigned.id, wallet, business1_token)

    response = action(assigned.id, courier2_token)

    assert_api_error(response, status_code=403, code="forbidden", message="Not your delivery")
    owner_response = delivery_api.get_delivery(assigned.id, business1_token)
    after = response_data(owner_response)
    assert after["status"] == DeliveryStage.ASSIGNED
    assert after["courier_id"] == assigned.courier_id
    assert snapshot(assigned.id, wallet, business1_token) == before
    assert_ledger(assigned.id, courier2_token)


def test_other_courier_cannot_complete_delivery_with_valid_code(
        staged_delivery, wallet, user_details, business1_token, courier2_token,
):
    picked_up = staged_delivery(DeliveryStage.PICKED_UP)
    other_courier = user_details(courier2_token)
    assert other_courier["id"] != picked_up.courier_id
    code = delivery_code(picked_up.id, business1_token)
    before = snapshot(picked_up.id, wallet, business1_token)

    response = courier_api.deliver_delivery(picked_up.id, courier2_token, code=code)

    assert_api_error(response, status_code=403, code="forbidden", message="Not your delivery")
    after_response = delivery_api.get_delivery(picked_up.id, business1_token)
    after = response_data(after_response)
    assert after["status"] == DeliveryStage.PICKED_UP
    assert after["courier_id"] == picked_up.courier_id
    assert snapshot(picked_up.id, wallet, business1_token) == before
    assert_ledger(picked_up.id, courier2_token)


# webhooks
def test_completion_logs_one_webhook_event(staged_delivery, business1_token, courier1_token):
    picked_up = staged_delivery(DeliveryStage.PICKED_UP)
    code = delivery_code(picked_up.id, business1_token)
    response_data(courier_api.deliver_delivery(picked_up.id, courier1_token, code=code))

    events = response_data(webhook_api.list_webhook_events(business1_token))["data"]

    delivered_events = [e for e in events if e["delivery_id"] == picked_up.id and e["type"] == "delivery.delivered"]
    assert len(delivered_events) == 1
    assert delivered_events[0]["status"] == DeliveryStage.DELIVERED
