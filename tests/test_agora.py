import locale
import os
from datetime import date

import pytest

from agora.automation import SlotColor, _full_month_french, _get_slot_color

# Check if running in GitHub Actions
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def test_get_slot_color():
    assert _get_slot_color("rgb(250, 252, 249)") is SlotColor.white
    assert _get_slot_color("rgb(147, 212, 123)") is SlotColor.green
    assert _get_slot_color("rgb(246, 217, 109)") is SlotColor.yellow
    assert _get_slot_color("rgb(241, 114, 130") is SlotColor.red


@pytest.mark.skipif(
    IN_GITHUB_ACTIONS,
    reason="Test does not work in GitHub Actions due to missing locale.",
)
def test_full_month_french():
    locale.setlocale(locale.LC_ALL, "fr_FR")
    for m in range(1, 13):
        d = date(2026, m, 12)
        assert _full_month_french(d) == d.strftime("%B")
