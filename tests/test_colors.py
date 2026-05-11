"""Tests for renderers.html.colors.bar_color().

Five colour cases:
  grey   — Declined status
  red    — start or end >8 days past due date
  orange — start >1 day past due date (but not red)
  yellow — end after due date (but not orange/red)
  green  — on time, or no due date
"""

from datetime import datetime
from typing import Optional

import pytest

from models import ChildIssue
from renderers.html.colors import bar_color

# ── Helpers ───────────────────────────────────────────────────────────


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def _make(
    status: str = "In Progress",
    start_date: Optional[str] = None,
    done_date: Optional[str] = None,
    due_date: Optional[str] = None,
) -> ChildIssue:
    return ChildIssue(
        key="HE-1",
        summary="Test issue",
        status=status,
        created=_iso(datetime(2025, 1, 1)),
        updated=_iso(datetime(2025, 1, 2)),
        start_date=start_date,
        done_date=done_date,
        due_date=due_date,
    )


# Fixed reference point so tests are deterministic
TODAY = datetime(2025, 6, 15)
DUE   = datetime(2025, 6, 10)  # 5 days before TODAY


# ── Grey (Declined) ───────────────────────────────────────────────────


def test_grey_declined_no_dates():
    item = _make(status="Declined")
    assert bar_color(item, TODAY) == ("#90A4AE", "grey")


def test_grey_declined_with_due_date():
    """Declined always grey regardless of dates."""
    item = _make(status="Declined", start_date=_iso(DUE), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#90A4AE", "grey")


def test_grey_declined_case_insensitive():
    item = _make(status="DECLINED")
    assert bar_color(item, TODAY) == ("#90A4AE", "grey")


# ── Green (no due date or on time) ───────────────────────────────────


def test_green_no_due_date():
    item = _make(start_date=_iso(datetime(2025, 6, 1)), done_date=_iso(datetime(2025, 6, 5)))
    assert bar_color(item, TODAY) == ("#27AE60", "green")


def test_green_done_before_due():
    start = datetime(2025, 6, 1)
    end   = datetime(2025, 6, 8)   # before DUE (Jun 10)
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#27AE60", "green")


def test_green_done_exactly_on_due():
    start = datetime(2025, 6, 1)
    end   = DUE
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#27AE60", "green")


def test_green_open_item_not_yet_past_due():
    """Open item where today is before the due date."""
    future_due = datetime(2025, 7, 1)
    item = _make(start_date=_iso(datetime(2025, 6, 1)), due_date=_iso(future_due))
    assert bar_color(item, TODAY) == ("#27AE60", "green")


# ── Yellow (end after due, no late-start) ─────────────────────────────


def test_yellow_done_one_day_after_due():
    start = datetime(2025, 6, 1)
    end   = datetime(2025, 6, 11)  # 1 day after DUE
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#FAD335", "yellow")


def test_yellow_open_item_today_after_due():
    """Open item where today (TODAY=Jun 15) is after due (DUE=Jun 10)."""
    start = datetime(2025, 6, 1)
    item = _make(start_date=_iso(start), due_date=_iso(DUE))
    # end defaults to TODAY (Jun 15), which is after DUE (Jun 10) but (15-10)=5 ≤ 8
    assert bar_color(item, TODAY) == ("#FAD335", "yellow")


def test_yellow_boundary_end_exactly_8_days_late():
    """end - due == 8 days is NOT red (need >8); start is before due → yellow."""
    start = datetime(2025, 6, 1)   # well before DUE
    end   = datetime(2025, 6, 18)  # DUE + 8 days
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#FAD335", "yellow")


def test_yellow_boundary_start_exactly_1_day_late():
    """start - due == 1 day is NOT orange (need >1); end > due → yellow."""
    start = datetime(2025, 6, 11)  # DUE + 1
    end   = datetime(2025, 6, 14)  # after DUE but (14-10)=4 ≤ 8
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#FAD335", "yellow")


# ── Orange (started >1 day late, not red) ────────────────────────────


def test_orange_start_2_days_after_due():
    start = datetime(2025, 6, 12)  # DUE + 2
    end   = datetime(2025, 6, 14)  # (14-10)=4 ≤ 8, not red
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#F07509", "orange")


def test_orange_boundary_start_exactly_2_days_late():
    """>1 → orange (2 qualifies)."""
    start = datetime(2025, 6, 12)  # DUE + 2
    end   = datetime(2025, 6, 13)  # (13-10)=3 ≤ 8
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#F07509", "orange")


def test_orange_start_8_days_after_due_end_not_late_enough():
    """start=DUE+8 → (start-due)=8 which is NOT >8, so not red via start path.
    end=DUE+8 → (end-due)=8 which is also NOT >8, so not red via end path.
    start-due=8 >1 → orange."""
    start = datetime(2025, 6, 18)  # DUE + 8
    end   = datetime(2025, 6, 18)
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#F07509", "orange")


# ── Red (>8 days late) ────────────────────────────────────────────────


def test_red_end_9_days_after_due():
    start = datetime(2025, 6, 1)
    end   = datetime(2025, 6, 19)  # DUE + 9
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#C0392B", "red")


def test_red_start_9_days_after_due():
    """Even if end is close to due, late start (>8 days) triggers red."""
    start = datetime(2025, 6, 19)  # DUE + 9
    end   = datetime(2025, 6, 20)
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#C0392B", "red")


def test_red_boundary_end_exactly_9_days_late():
    """>8 → red (9 qualifies)."""
    start = datetime(2025, 6, 1)
    end   = datetime(2025, 6, 19)  # DUE + 9
    item = _make(start_date=_iso(start), done_date=_iso(end), due_date=_iso(DUE))
    assert bar_color(item, TODAY) == ("#C0392B", "red")


def test_red_open_item_today_9_days_after_due():
    """Open item where today is 9 days past due → red."""
    today_9_late = datetime(2025, 6, 19)  # DUE + 9
    start = datetime(2025, 6, 1)
    item = _make(start_date=_iso(start), due_date=_iso(DUE))
    assert bar_color(item, today_9_late) == ("#C0392B", "red")


# ── Return type ───────────────────────────────────────────────────────


def test_returns_tuple_of_two_strings():
    item = _make()
    result = bar_color(item, TODAY)
    assert isinstance(result, tuple)
    assert len(result) == 2
    color_hex, color_key = result
    assert color_hex.startswith("#")
    assert color_key in {"green", "yellow", "orange", "red", "grey"}
