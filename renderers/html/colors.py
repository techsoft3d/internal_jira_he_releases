"""Bar colour logic for Gantt chart items.

Five colour cases (in priority order):
  grey   — Declined status
  red    — start or end is more than 8 days past the due date
  orange — start is more than 1 day past the due date
  yellow — end is after the due date
  green  — on time, or no due date
"""

from datetime import datetime
from typing import Tuple

from models import ChildIssue
from utils import parse_date

# (hex_color, color_key)
_GREEN  = ("#27AE60", "green")
_YELLOW = ("#FAD335", "yellow")
_ORANGE = ("#F07509", "orange")
_RED    = ("#C0392B", "red")
_GREY   = ("#90A4AE", "grey")


def bar_color(item: ChildIssue, today: datetime) -> Tuple[str, str]:
    """Return ``(hex_color, color_key)`` for a child issue's Gantt bar.

    *today* is used as the end date for items that are not yet done.
    """
    if item.status.lower() == "declined":
        return _GREY

    due_dt = parse_date(item.due_date)
    if due_dt is None:
        return _GREEN

    start = parse_date(item.start_date)
    end = parse_date(item.done_date) or today

    if start is not None and (
        (end - due_dt).days > 8 or (start - due_dt).days > 8
    ):
        return _RED

    if start is not None and (start - due_dt).days > 1:
        return _ORANGE

    if end > due_dt:
        return _YELLOW

    return _GREEN
