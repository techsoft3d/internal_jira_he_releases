"""Gantt chart HTML fragment for one release."""

from datetime import datetime, timedelta
from typing import List

from models import ChildIssue, Epic
from renderers.html.colors import bar_color
from utils import esc, fmt_date, parse_date

# Release cards are shown in dependency order based on these summary keywords.
_RELEASE_ORDER_KEYWORDS = [
    "define a squad",           # 1. Choose squad
    "create release branch",    # 2. Branch creation
    "deliver",                  # 3. Deliver RC1
    "test plan",                # 4. Test plan tasks
    "test he in production",    # 5. Test staging
    "close the release",        # 6. Close release
]


def _release_sort_key(item: dict) -> tuple:
    """Place known release cards in dependency order; unknown ones by date."""
    summary_lower = item["summary"].lower()
    for idx, keyword in enumerate(_RELEASE_ORDER_KEYWORDS):
        if keyword in summary_lower:
            return (idx, item["_start"], item["_end"])
    return (len(_RELEASE_ORDER_KEYWORDS), item["_start"], item["_end"])


def build_gantt_html(epic: Epic, children: List[ChildIssue], jira_url: str) -> str:
    """Return an HTML fragment with a Gantt chart for one release."""
    today = datetime.now()

    items = []
    for c in children:
        start = parse_date(c.start_date)
        end = parse_date(c.done_date) or today
        if start is None:
            continue
        if end < start:
            end = start
        color, color_key = bar_color(c, today)
        items.append({
            "key": c.key,
            "summary": c.summary,
            "status": c.status,
            "priority": c.priority,
            "assignee": c.assignee,
            "start_date": c.start_date,
            "done_date": c.done_date,
            "due_date": c.due_date,
            "_start": start,
            "_end": end,
            "_color": color,
            "_color_key": color_key,
        })

    if not items:
        return '<p><em>No timeline data (no dates available).</em></p>'

    items.sort(key=_release_sort_key)

    min_date = min(i["_start"] for i in items)
    max_date = max(i["_end"] for i in items)
    span_days = max((max_date - min_date).days, 1)

    # Date axis — at most ~16 labels
    step = max(span_days // 16, 1)
    axis_labels = []
    d = min_date
    while d <= max_date:
        pct = (d - min_date).days / span_days * 100
        axis_labels.append((pct, d.strftime("%b %d")))
        d += timedelta(days=step)

    lines: List[str] = []
    lines.append('<div class="timeline-container">')

    lines.append('<div class="timeline-axis">')
    for pct, label in axis_labels:
        lines.append(f'<span class="axis-label" style="left:{pct:.1f}%">{label}</span>')
    lines.append('</div>')

    for item in items:
        left = (item["_start"] - min_date).days / span_days * 100
        width = max((item["_end"] - item["_start"]).days / span_days * 100, 0.5)
        is_open = item["done_date"] is None
        bar_class = "timeline-bar open" if is_open else "timeline-bar"

        assignee = esc(item["assignee"] or "Unassigned")
        due_date_str = item["due_date"]

        due_marker_html = ""
        if due_date_str:
            due_dt = parse_date(due_date_str)
            if due_dt is not None:
                due_pct = max(0.0, min(100.0, (due_dt - min_date).days / span_days * 100))
                due_marker_html = (
                    f'<div class="due-date-marker" '
                    f'style="left:{due_pct:.2f}%" '
                    f'title="Due: {fmt_date(due_date_str)}"></div>'
                )

        tooltip = (
            f'{esc(item["key"])} — {esc(item["summary"])}\n'
            f'Status: {esc(item["status"])}  |  {esc(item["priority"] or "")}\n'
            f'Development: {fmt_date(item["start_date"])}  →  '
            f'Done: {fmt_date(item["done_date"])}\n'
            + (f'Due: {fmt_date(due_date_str)}\n' if due_date_str else "")
            + f'Assignee: {assignee}'
        )
        label_text = f'{esc(item["key"])} {esc(item["summary"][:50])}'
        card_url = f'{jira_url}/browse/{esc(item["key"])}'
        duration_days = (item["_end"] - item["_start"]).days

        lines.append(
            f'<div class="timeline-row" data-color-key="{item["_color_key"]}">'
            f'<div class="timeline-label" title="{tooltip}">'
            f'<a href="{card_url}" target="_blank" class="card-link">{label_text}</a></div>'
            f'<div class="timeline-track">'
            f'{due_marker_html}'
            f'<div class="{bar_class}" '
            f'style="left:{left:.2f}%;width:{width:.2f}%;background:{item["_color"]}" '
            f'title="{tooltip}">'
            f'<span class="bar-dates">{duration_days}d</span>'
            f'</div></div></div>'
        )

    lines.append('</div>')
    return "\n".join(lines)
