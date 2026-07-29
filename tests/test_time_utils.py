"""Tests for time utility functions."""

from __future__ import annotations

import pytest

from src.utils.time_utils import (
    days_mapper,
    military_time_range_to_ampm,
    parse_start_hour,
    spanish_day_mapper,
)


class TestDaysMapper:
    def test_monday_returns_zero(self) -> None:
        assert days_mapper("monday") == 0

    def test_sunday_returns_six(self) -> None:
        assert days_mapper("sunday") == 6

    def test_case_insensitive(self) -> None:
        assert days_mapper("Monday") == 0
        assert days_mapper("MONDAY") == 0

    def test_invalid_day_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid day"):
            days_mapper("invalid")


class TestSpanishDayMapper:
    def test_monday_returns_lunes(self) -> None:
        assert spanish_day_mapper("monday") == "lunes"

    def test_sunday_returns_domingo(self) -> None:
        assert spanish_day_mapper("sunday") == "domingo"

    def test_invalid_day_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid day"):
            spanish_day_mapper("invalid")


class TestParseStartHour:
    def test_standard_range(self) -> None:
        assert parse_start_hour("07:00 - 08:00") == (7, 0)

    def test_single_digit_hour(self) -> None:
        assert parse_start_hour("06:30 - 07:30") == (6, 30)

    def test_midday(self) -> None:
        assert parse_start_hour("12:00 - 13:00") == (12, 0)

    def test_invalid_format_raises_value_error(self) -> None:
        with pytest.raises((ValueError, IndexError)):
            parse_start_hour("invalid")


class TestMilitaryTimeRangeToAmPm:
    def test_morning_range(self) -> None:
        assert military_time_range_to_ampm("07:00 - 08:00") == "07:00 AM - 08:00 AM"

    def test_afternoon_range(self) -> None:
        assert military_time_range_to_ampm("15:00 - 16:00") == "03:00 PM - 04:00 PM"

    def test_noon_edge(self) -> None:
        assert military_time_range_to_ampm("12:00 - 13:00") == "12:00 PM - 01:00 PM"

    def test_midnight_edge(self) -> None:
        assert military_time_range_to_ampm("00:00 - 01:00") == "12:00 AM - 01:00 AM"

    def test_invalid_format_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid time format"):
            military_time_range_to_ampm("invalid")
