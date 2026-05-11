"""Tests for utils.py — pure utility functions."""

import pytest
from datetime import datetime

from utils import esc, extract_version, fmt_date, parse_date


class TestExtractVersion:
    def test_three_part_version(self):
        assert extract_version("[2026.3.0] HE Core release") == (2026, 3, 0)

    def test_two_part_version(self):
        assert extract_version("[2026.3] HE Core release") == (2026, 3)

    def test_no_bracket_tag(self):
        assert extract_version("HE Core release no version") == (0,)

    def test_empty_string(self):
        assert extract_version("") == (0,)

    def test_version_at_end(self):
        assert extract_version("HE Core release [2025.1.0]") == (2025, 1, 0)

    def test_multiple_brackets_picks_first(self):
        # Only the first bracketed version should be extracted
        assert extract_version("[2026.3.0] HE [2025.1.0] release") == (2026, 3, 0)

    def test_sorting_by_extracted_version(self):
        summaries = [
            "[2025.3.0] HE",
            "[2026.1.0] HE",
            "[2025.10.0] HE",
        ]
        sorted_summaries = sorted(summaries, key=extract_version, reverse=True)
        assert sorted_summaries[0] == "[2026.1.0] HE"
        assert sorted_summaries[1] == "[2025.10.0] HE"
        assert sorted_summaries[2] == "[2025.3.0] HE"


class TestFmtDate:
    def test_iso_with_offset(self):
        assert fmt_date("2026-03-15T10:30:00+00:00") == "2026-03-15"

    def test_iso_with_z(self):
        assert fmt_date("2026-03-15T10:30:00Z") == "2026-03-15"

    def test_date_only(self):
        assert fmt_date("2026-03-15") == "2026-03-15"

    def test_none_returns_dash(self):
        assert fmt_date(None) == "—"

    def test_empty_string_returns_dash(self):
        assert fmt_date("") == "—"

    def test_malformed_falls_back_to_first_10_chars(self):
        assert fmt_date("2026-03-15garbage") == "2026-03-15"

    def test_completely_invalid_truncates(self):
        assert fmt_date("no-valid-date-here") == "no-valid-d"


class TestParseDate:
    def test_iso_with_offset(self):
        result = parse_date("2026-03-15T10:30:00+00:00")
        assert result == datetime(2026, 3, 15, 10, 30, 0)
        assert result.tzinfo is None  # must be naive

    def test_iso_with_z(self):
        result = parse_date("2026-03-15T10:30:00Z")
        assert result == datetime(2026, 3, 15, 10, 30, 0)

    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_empty_string_returns_none(self):
        assert parse_date("") is None

    def test_malformed_returns_none(self):
        assert parse_date("not-a-date") is None

    def test_result_is_naive(self):
        result = parse_date("2026-03-15T10:30:00+05:00")
        assert result is not None
        assert result.tzinfo is None


class TestEsc:
    def test_none_returns_empty_string(self):
        assert esc(None) == ""

    def test_plain_text_unchanged(self):
        assert esc("hello world") == "hello world"

    def test_ampersand(self):
        assert esc("A & B") == "A &amp; B"

    def test_less_than(self):
        assert esc("<script>") == "&lt;script&gt;"

    def test_greater_than(self):
        assert esc("x > y") == "x &gt; y"

    def test_double_quote(self):
        assert esc('say "hi"') == "say &quot;hi&quot;"

    def test_all_special_chars(self):
        assert esc('<a href="x&y">') == "&lt;a href=&quot;x&amp;y&quot;&gt;"

    def test_non_string_input(self):
        assert esc(42) == "42"
