from utils.constant_data import DeliveryStage


def test_jik(business1_token, wallet):
    wallet(business1_token)

def test_stage(staged_delivery):
    print(staged_delivery(DeliveryStage.ASSIGNED))