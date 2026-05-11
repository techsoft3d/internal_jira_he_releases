"""
Full HTML page builder for release timelines.
Assembles TOC + per-release Gantt sections with minimal inline CSS.
"""

from datetime import datetime
from typing import List, Tuple

from models import ChildIssue, Epic
from utils import esc, fmt_date, parse_date
from renderers.html.gantt import build_gantt_html

_CSS = """\
body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 2rem; background: #f5f5f5; }
h1 { color: #1a237e; }
.release { background: #fff; border-radius: 8px; padding: 1.2rem 1.5rem;
           margin-bottom: 1.5rem; box-shadow: 0 2px 6px rgba(0,0,0,.1); }
.release h2 { margin: 0 0 .3rem; font-size: 1.25rem; }
.meta { color: #666; font-size: .85rem; margin-bottom: .8rem; }
.progress-bar { background: #e0e0e0; border-radius: 6px; height: 14px;
                overflow: hidden; max-width: 400px; margin-bottom: .8rem; }
.progress-fill { height: 100%; border-radius: 6px; background: #4A90D9; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
         color: #fff; font-size: .78rem; font-weight: 600; background: #9E9E9E; }
.toc { margin-bottom: 2rem; }
.toc a { text-decoration: none; color: #1a237e; }
.toc a:hover { text-decoration: underline; }
.card-link { text-decoration: none; color: #1a237e; }
.card-link:hover { text-decoration: underline; }
h3.timeline-heading { margin: 1.4rem 0 .3rem; color: #37474f; font-size: 1rem; }
/* Gantt */
.timeline-container { margin: 1.2rem 0 .5rem; position: relative; }
.timeline-axis { position: relative; height: 22px; border-bottom: 1px solid #ccc;
                 margin-left: 320px; margin-bottom: 4px; }
.axis-label { position: absolute; top: 0; font-size: .7rem; color: #888;
              transform: translateX(-50%); white-space: nowrap; }
.timeline-row { display: flex; align-items: center; margin-bottom: 3px; min-height: 28px; }
.timeline-label { width: 320px; flex-shrink: 0; font-size: .78rem; color: #333;
                  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                  padding-right: 8px; }
.timeline-track { flex: 1; position: relative; height: 22px;
                  background: repeating-linear-gradient(
                    90deg, #f0f0f0 0px, #f0f0f0 1px, transparent 1px, transparent 50px
                  ); border-radius: 3px; }
.timeline-bar { position: absolute; top: 2px; height: 18px; border-radius: 4px;
                min-width: 4px; cursor: pointer; opacity: .9; transition: opacity .15s;
                display: flex; align-items: center; overflow: hidden; }
.timeline-bar:hover { opacity: 1; box-shadow: 0 1px 6px rgba(0,0,0,.25); z-index: 2; }
.timeline-bar.open { background-image: repeating-linear-gradient(
    -45deg, transparent, transparent 4px, rgba(255,255,255,.25) 4px,
    rgba(255,255,255,.25) 8px) !important; }
.bar-dates { font-size: .65rem; color: #fff; padding: 0 6px; white-space: nowrap;
             text-shadow: 0 1px 2px rgba(0,0,0,.4); }
.due-date-marker { position: absolute; top: 0; bottom: 0; width: 2px;
                   background: #C0392B; z-index: 3; pointer-events: none;
                   box-shadow: 0 0 3px rgba(192,57,43,.6); }
"""


def build_html(releases: List[Tuple[Epic, List[ChildIssue]]], jira_url: str) -> str:
    """Return a full HTML page with a TOC and a Gantt chart per release."""
    parts: List[str] = []
    parts.append(
        f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>Jira Release Timelines</title>\n'
        f'<style>\n{_CSS}</style></head><body>\n'
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

    # One section per release
    for epic, children in releases:
        done = sum(1 for c in children if c.status.upper() == "DONE")
        total = len(children)
        pct = int(done / total * 100) if total else 0

        # Optional span summary (first dev start → last done)
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
            f' <span class="badge">{esc(epic.status)}</span>'
            f'{span_text}</h2>'
        )
        parts.append(
            f'<div class="meta">{esc(epic.key)} · '
            f'Created {fmt_date(epic.created)} · '
            f'Updated {fmt_date(epic.updated)}</div>'
        )
        parts.append(
            f'<div class="progress-bar">'
            f'<div class="progress-fill" style="width:{pct}%"></div>'
            f'</div>'
        )
        parts.append(f'<div class="meta">{pct}% complete ({done}/{total} items)</div>')

        if children:
            parts.append('<h3 class="timeline-heading">Timeline</h3>')
            parts.append(build_gantt_html(epic, children, jira_url))
        else:
            parts.append('<p><em>No child items found.</em></p>')

        parts.append('</div>')

    parts.append('</body></html>')
    return "\n".join(parts)
