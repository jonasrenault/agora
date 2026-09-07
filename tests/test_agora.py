from agora.agora import SlotColor, _get_slot_color


def test_get_slot_color():
    assert _get_slot_color("rgb(250, 252, 249)") is SlotColor.white
    assert _get_slot_color("rgb(147, 212, 123)") is SlotColor.green
    assert _get_slot_color("rgb(246, 217, 109)") is SlotColor.yellow
    assert _get_slot_color("rgb(241, 114, 130") is SlotColor.red
