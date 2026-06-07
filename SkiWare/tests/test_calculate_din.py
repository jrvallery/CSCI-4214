import pytest

from backend.services.calculate_DIN import calculate_din, get_din, parse_weight


def test_parse_weight_converts_pounds_to_kilograms():
    assert parse_weight("170 lbs") == pytest.approx(77.11064)


def test_calculate_din_matches_expected_chart_value():
    assert calculate_din(weight="170 lbs", boot_sole_length_mm=290, age=21, skier_type=3) == 8.5


def test_get_din_keeps_script_compatible_signature():
    assert get_din(weight=60, boot=290, age=55, skier_type=1) == 4.0


def test_calculate_din_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_din(weight="unknown", boot_sole_length_mm=290, age=21, skier_type=2)

    with pytest.raises(ValueError):
        calculate_din(weight=70, boot_sole_length_mm=290, age=21, skier_type=4)
