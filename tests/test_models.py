import json
from datetime import datetime

from agora.api.models import GooglePubSubPayload, User


def test_user_remove_slots():
    dates = [
        datetime.strptime(v.strip(), "%d/%m/%Y").date()
        for v in "25/10/2026, 19/01/1987, 30/12/2017".split(",")
    ]
    user = User(email="test@test.fr", hashed_password="", agora_slots=dates)

    user.remove_slots([dates[1]])
    assert user.agora_slots == [dates[0], dates[2]]
    user.remove_slots([dates[2]])
    assert user.agora_slots == [dates[0]]
    user.remove_slots([dates[0]])
    assert user.agora_slots is None


def test_google_pub_sub_payload_parse():
    input = {
        "message": {
            "data": "eyJlbWFpbEFkZHJlc3MiOiAidXNlckBleGFtcGxlLmNvbSIsICJoaXN0b3J5SWQiOiAiMTIzNDU2Nzg5MCJ9",  # noqa: E501
            "messageId": "2070443601311540",
            "publishTime": "2021-02-26T19:13:55.749Z",
        },
        "subscription": "projects/myproject/subscriptions/mysubscription",
    }

    payload = GooglePubSubPayload.model_validate_json(json.dumps(input))
    assert payload.message.data.email == "user@example.com"
    assert payload.message.data.history_id == "1234567890"
