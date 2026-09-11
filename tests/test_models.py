from datetime import datetime

from agora.api.models import User


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
