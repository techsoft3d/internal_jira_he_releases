"""Full HTML page builder for release timelines."""

from datetime import datetime
from typing import List, Tuple

from models import ChildIssue, Epic
from renderers.html.gantt import build_gantt_html
from renderers.html.styles import CSS, JS, STATUS_COLORS
from utils import esc, fmt_date, parse_date

_LEGEND = (
    '<div class="legend">'
    '<span class="legend-title">Bar colour (click to filter):</span>'
    '<button class="legend-filter" data-filter="green">'
    '<span class="legend-swatch" style="background:#27AE60"></span>On time / no due date</button>'
    '<button class="legend-filter" data-filter="yellow">'
    '<span class="legend-swatch" style="background:#FAD335"></span>Ends after due date</button>'
    '<button class="legend-filter" data-filter="orange">'
    '<span class="legend-swatch" style="background:#F07509"></span>Started after due date</button>'
    '<button class="legend-filter" data-filter="red">'
    '<span class="legend-swatch" style="background:#C0392B"></span>Late &gt;8 days</button>'
    '<button class="legend-filter" data-filter="grey">'
    '<span class="legend-swatch" style="background:#90A4AE"></span>Declined</button>'
    '<span class="legend-item"><span class="legend-marker"></span>Due date marker</span>'
    '</div>'
)


def build_html(releases: List[Tuple[Epic, List[ChildIssue]]], jira_url: str) -> str:
    """Return a full HTML page with a TOC, legend, and a Gantt chart per release."""
    parts: List[str] = []
    parts.append(
        f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>Jira Release Timelines</title>\n'
        f'<style>\n{CSS}</style></head><body>\n'
        f'<h1>Jira Release Timelines</h1>\n'
        f'<p class="meta">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>\n'
    )

    # Table of contents
    parts.append('<div class="toc"><h3>Releases</h3><ol>')
    for epic, children in releases:
        done = sum(1 for c in children if c.status.upper() == "DONE")
        total = len(children)
        parts.append(
            f'<li><a href="#{esc(epic.key)}">{esc(epic.summary)}</a>'
            f' — {esc(epic.status)} ({done}/{total})</li>'
        )
    parts.append('</ol></div>\n')

    parts.append(_LEGEND)

    # One section per release
    for epic, children in releases:
        status_color = STATUS_COLORS.get(epic.status, "#9E9E9E")
        done = sum(1 for c in children if c.status.upper() == "DONE")
        total = len(children)
        pct = int(done / total * 100) if total else 0

        span_text = ""
        if children:
            starts = [dt for c in children if (dt := parse_date(c.start_date)) is not None]
            ends = [dt for c in children if (dt := parse_date(c.done_date)) is not None]
            if starts and ends:
                first_start = min(starts)
                last_end = max(ends)
                total_days = (last_end - first_start).days
                span_text = (
                    f' <span style="font-size:.85rem;color:#555;font-weight:normal">'
                    f'— {total_days} days '
                    f'({first_start.strftime("%b %d")} → {last_end.strftime("%b %d")})</span>'
                )

        epic_url = f'{jira_url}/browse/{esc(epic.key)}'
        parts.append(f'<div class="release" id="{esc(epic.key)}">')
        parts.append(
            f'<h2><a href="{epic_url}" target="_blank" class="card-link">'
            f'{esc(epic.summary)}</a>'
            f' <span class="badge" style="background:{status_color}">{esc(epic.status)}</span>'
            f'{span_text}</h2>'
        )
        parts.append(
            f'<div class="meta">{esc(epic.key)} · '
            f'Created {fmt_date(epic.created)} · '
            f'Updated {fmt_date(epic.updated)}</div>'
        )
        parts.append(
            f'<div class="progress-bar">'
            f'<div class="progress-fill" style="width:{pct}%;background:{status_color}"></div>'
            f'</div>'
        )
        parts.append(f'<div class="meta">{pct}% complete ({done}/{total} items)</div>')

        if children:
            parts.append('<h3 class="timeline-heading">Timeline</h3>')
            parts.append(build_gantt_html(epic, children, jira_url))
        else:
            parts.append('<p><em>No child items found.</em></p>')

        parts.append('</div>')

    parts.append(JS)
    parts.append('</body></html>')
    return "\n".join(parts)
