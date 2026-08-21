"""Regression tests for manufacturer presets observed in SmartControl captures."""

from __future__ import annotations

import struct
import sys
import unittest
from unittest.mock import Mock, patch

import conftest  # noqa: F401 - install the existing Home Assistant test stubs

sys.path.insert(0, "custom_components")

from comfospot.client import ComfoSpot, ComfoSpotError
from comfospot.const import (
    PID_MODE,
    PID_MODE_UNTIL,
    PID_SPEED,
    PRESET_AUTOMATIC,
    PRESET_BOOST,
    PRESET_NIGHT,
    PRESET_NORMAL,
)


class ManufacturerPresetTests(unittest.TestCase):
    """Assert exact property payloads, preserving direction and fan speed."""

    def setUp(self) -> None:
        self.api = ComfoSpot("192.168.178.57")
        self.connection = Mock()
        self.connection.is_alive.return_value = True
        self.connection.set_properties.return_value = {"result": 0}
        self.connection.set_property.return_value = {"result": 0}
        self.connection.state = {
            (10, PID_MODE): (6, b"\x02"),
            (10, PID_SPEED): (9, struct.pack("<f", 1.6)),
        }
        self.api._client = self.connection

    @patch("comfospot.client.time.time", return_value=1_700_000_000)
    def test_night_mode_matches_captured_vendor_command(self, _clock: Mock) -> None:
        self.api.set_preset(10, PRESET_NIGHT, 60)

        self.connection.set_properties.assert_called_once_with(
            10,
            [
                (10, PID_MODE_UNTIL, struct.pack("<I", 1_700_003_600)),
                (6, PID_MODE, b"\x10"),
                (9, PID_SPEED, struct.pack("<f", 0.0)),
            ],
        )
        self.assertAlmostEqual(self.api.last_active_stage(10), 1.6)
        self.assertEqual(self.api._last_directions[10], 2)

    @patch("comfospot.client.time.time", return_value=1_700_000_000)
    def test_boost_mode_lets_the_hub_select_maximum_speed(self, _clock: Mock) -> None:
        self.api.set_preset(10, PRESET_BOOST, 30)

        self.connection.set_properties.assert_called_once_with(
            10,
            [
                (10, PID_MODE_UNTIL, struct.pack("<I", 1_700_001_800)),
                (6, PID_MODE, b"\x20"),
            ],
        )

    def test_automatic_mode_sets_only_the_preset_nibble(self) -> None:
        self.api.set_preset(10, PRESET_AUTOMATIC)

        properties = self.connection.set_properties.call_args.args[1]
        self.assertEqual(properties[0], (6, PID_MODE, b"\x30"))
        self.assertEqual(properties[1][0:2], (9, PID_SPEED))
        self.assertAlmostEqual(struct.unpack("<f", properties[1][2])[0], 1.6)

    def test_normal_mode_restores_previous_direction_and_speed(self) -> None:
        self.connection.state = {
            (10, PID_MODE): (6, b"\x10"),
            (10, PID_SPEED): (9, struct.pack("<f", 0.0)),
        }
        self.api._last_directions[10] = 2
        self.api._last_active_stages[10] = 1.6

        self.api.set_preset(10, PRESET_NORMAL)

        properties = self.connection.set_properties.call_args.args[1]
        self.assertEqual(properties[0], (10, PID_MODE_UNTIL, b"\x00" * 4))
        self.assertEqual(properties[1], (6, PID_MODE, b"\x02"))
        self.assertAlmostEqual(struct.unpack("<f", properties[2][2])[0], 1.6)

    def test_direction_change_preserves_automatic_mode(self) -> None:
        self.connection.state[(10, PID_MODE)] = (6, b"\x32")

        self.api.set_mode(10, 1)

        self.connection.set_property.assert_called_once_with(
            10, 6, PID_MODE, b"\x31"
        )

    def test_set_stage_exits_night_mode_and_restores_direction(self) -> None:
        self.connection.state[(10, PID_MODE)] = (6, b"\x10")
        self.api._last_directions[10] = 2

        self.api.set_stage(10, 1.6)

        properties = self.connection.set_properties.call_args.args[1]
        self.assertEqual(properties[0], (10, PID_MODE_UNTIL, b"\x00" * 4))
        self.assertEqual(properties[1], (6, PID_MODE, b"\x02"))
        self.assertAlmostEqual(struct.unpack("<f", properties[2][2])[0], 1.6)

    def test_zero_stage_requires_the_vendor_night_mode(self) -> None:
        with self.assertRaises(ComfoSpotError):
            self.api.set_stage(10, 0)

    def test_timed_presets_require_a_duration(self) -> None:
        for preset in (PRESET_NIGHT, PRESET_BOOST):
            with self.subTest(preset=preset):
                with self.assertRaises(ComfoSpotError):
                    self.api.set_preset(10, preset)


if __name__ == "__main__":
    unittest.main()
