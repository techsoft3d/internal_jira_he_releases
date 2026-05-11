"""
Standalone script: Fetch Jira release epics and build a visual timeline
for each release's child work items.

Usage:
    python release_timeline.py [--output html|console] [--search "HE CORE release"]
    python release_timeline.py --year 2026
    python release_timeline.py --release 2026.3.0
    python release_timeline.py --release 2026.3.0 --output html
"""

import argparse
import configparser
import re
import sys
from datetime import datetime
from pathlib import Path

from jira import JIRA

# ── Jira authentication ────────────────────────────────────────────────


def connect_jira(config_path: str = "config.ini") -> JIRA:
    """Authenticate to Jira using credentials from config.ini."""
    config = configparser.ConfigParser()
    if not Path(config_path).exists():
        sys.exit(f"Config file not found: {config_path}")
    config.read(config_path)

    url = config["jira"]["url"]
    user = config["jira"]["username"]
    token = config["jira"]["api_token"]

    jira = JIRA(
        options={"server": url, "rest_api_version": "3"},
        basic_auth=(user, token),
    )
    print(f"Connected to {url}")
    return jira


# ── Data fetching ──────────────────────────────────────────────────────


def fetch_release_epics(
    jira: JIRA,
    search_text: str,
    year: str | None = None,
    release: str | None = None,
) -> list[dict]:
    """
    Fetch release epics matching *search_text* in the HE / Exchange project.
    Optionally filter by --year (e.g. "2026") or --release (e.g. "2026.3.0").
    Returns a list of dicts with key, summary, status, created, updated.
    """
    jql = (
        f'project = HE AND type = Epic AND summary ~ "{search_text}" '
        f"ORDER BY created DESC"
    )
    print(f"JQL (epics): {jql}")
    epics_raw = jira.search_issues(jql, maxResults=100, fields="summary,status,created,updated")

    epics = []
    for e in epics_raw:
        status = e.fields.status
        epics.append(
            {
                "key": e.key,
                "summary": str(e.fields.summary),
                "status": status.name if hasattr(status, "name") else str(status),
                "created": str(e.fields.created),
                "updated": str(e.fields.updated),
            }
        )
    # Apply local filters (year / specific release version)
    if release:
        tag = f"[{release}]"  # e.g. "[2026.3.0]"
        epics = [e for e in epics if tag in e["summary"]]
    elif year:
        epics = [e for e in epics if f"[{year}" in e["summary"]]

    print(f"Found {len(epics)} release epic(s) after filtering")
    return epics


def _find_status_date(changelog_histories, target_status: str) -> str | None:
    """
    Walk the changelog and return the ISO timestamp of the first transition
    whose *to* status matches *target_status* (case-insensitive).
    Returns None if never found.
    """
    target = target_status.lower()
    for hist in changelog_histories:
        ts = hist.created  # ISO-8601 string
        for item in hist.items:
            if item.field == "status" and item.toString and item.toString.lower() == target:
                return str(ts)
    return None


def fetch_children(jira: JIRA, epic_key: str) -> list[dict]:
    """
    Fetch all child work items of *epic_key* with their changelog.
    The start_date is when the card was moved to "To Do" (falls back to created).
    """
    jql = f'"Parent" = {epic_key} ORDER BY created ASC'
    fields = (
        "summary,status,priority,assignee,story_points,"
        "customfield_10016,created,updated,resolutiondate,issuetype,duedate"
    )
    children_raw = jira.search_issues(
        jql, maxResults=200, fields=fields, expand="changelog"
    )

    children = []
    for c in children_raw:
        f = c.fields

        # Story points can live in standard or custom field
        sp = getattr(f, "story_points", None) or getattr(
            f, "customfield_10016", None
        )

        assignee_name = None
        if f.assignee:
            assignee_name = getattr(f.assignee, "displayName", None) or str(
                f.assignee
            )

        priority_name = None
        if f.priority:
            priority_name = (
                f.priority.name if hasattr(f.priority, "name") else str(f.priority)
            )

        status_obj = f.status
        status_name = (
            status_obj.name if hasattr(status_obj, "name") else str(status_obj)
        )

        issue_type = None
        if f.issuetype:
            issue_type = (
                f.issuetype.name
                if hasattr(f.issuetype, "name")
                else str(f.issuetype)
            )

        # Start date = when moved to "Development", fallback to created
        dev_date = _find_status_date(c.changelog.histories, "Development")
        start_date = dev_date or str(f.created)

        # End date = when moved to "Done", fallback to resolution date
        done_date = _find_status_date(c.changelog.histories, "Done")
        end_date = done_date or (
            str(f.resolutiondate) if f.resolutiondate else None
        )

        children.append(
            {
                "key": c.key,
                "summary": str(f.summary),
                "type": issue_type,
                "status": status_name,
                "priority": priority_name,
                "assignee": assignee_name,
                "story_points": sp,
                "start_date": start_date,
                "done_date": end_date,
                "due_date": str(f.duedate) if getattr(f, "duedate", None) else None,
                "created": str(f.created),
                "updated": str(f.updated),
                "resolution_date": str(f.resolutiondate)
                if f.resolutiondate
                else None,
            }
        )
    return children


# ── Version key extraction (for sorting) ───────────────────────────────


def extract_version(summary: str) -> tuple:
    """
    Pull the version tuple from a summary like '[2026.3.0] HE Core ...'.
    Returns e.g. (2026, 3, 0).  Falls back to (0,) if not found.
    """
    m = re.search(r"\[(\d+(?:\.\d+)+)\]", summary)
    if m:
        return tuple(int(x) for x in m.group(1).split("."))
    return (0,)


# ── Console rendering ─────────────────────────────────────────────────


STATUS_SYMBOLS = {
    "Done": "✅",
    "DONE": "✅",
    "Declined": "❌",
    "DECLINED": "❌",
    "Under Consideration": "🔵",
    "UNDER CONSIDERATION": "🔵",
    "In Progress": "🟡",
    "IN PROGRESS": "🟡",
    "To Do": "⬜",
    "TO DO": "⬜",
}


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(iso)[:10]


def print_timeline(epic: dict, children: list[dict]) -> None:
    """Print a text-based timeline for one release."""
    print()
    print("=" * 80)
    sym = STATUS_SYMBOLS.get(epic["status"], "⬜")
    print(f" {sym}  {epic['summary']}  ({epic['key']})  —  {epic['status']}")
    print(f"     Created: {_fmt_date(epic['created'])}   Updated: {_fmt_date(epic['updated'])}")
    print("-" * 80)

    if not children:
        print("     (no child work items)")
        print("=" * 80)
        return

    done = sum(1 for c in children if c["status"].upper() == "DONE")
    total = len(children)
    pct = int(done / total * 100) if total else 0
    bar_len = 40
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"     Progress: [{bar}] {pct}% ({done}/{total})")
    print("-" * 80)

    # Table header
    print(
        f"  {'Key':<12} {'Type':<12} {'Status':<22} {'Priority':<10} "
        f"{'SP':>3}  {'Dev Start':<12} {'Done':<12} {'Assignee'}"
    )
    print("  " + "─" * 76)

    for c in children:
        sym = STATUS_SYMBOLS.get(c["status"], "⬜")
        sp = str(c["story_points"]) if c["story_points"] else "—"
        assignee = c["assignee"] or "Unassigned"
        if len(assignee) > 14:
            assignee = assignee[:12] + ".."
        issue_type = c["type"] or ""
        if len(issue_type) > 10:
            issue_type = issue_type[:10] + ".."
        print(
            f"  {c['key']:<12} {issue_type:<12} {sym} {c['status']:<18} "
            f"{(c['priority'] or '—'):<10} {sp:>3}  "
            f"{_fmt_date(c['start_date']):<12} {_fmt_date(c['done_date']):<12} "
            f"{assignee}"
        )

    print("=" * 80)


# ── HTML rendering ─────────────────────────────────────────────────────


_STATUS_COLORS = {
    "Done": "#9E9E9E",
    "DONE": "#9E9E9E",
    "Declined": "#9E9E9E",
    "DECLINED": "#9E9E9E",
    "Under Consideration": "#2196F3",
    "UNDER CONSIDERATION": "#2196F3",
    "In Progress": "#FF9800",
    "IN PROGRESS": "#FF9800",
    "To Do": "#4CAF50",
    "TO DO": "#4CAF50",
}


def _esc(text: str | None) -> str:
    """Minimal HTML escaping."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _parse_date(iso: str | None) -> datetime | None:
    """Parse an ISO date string to a datetime, or None."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


# Release card ordering based on the release creation script's dependency chain.
# Cards whose summary contains these keywords get a fixed rank; unknown cards
# are placed at the end and sub-sorted by start date.
_RELEASE_ORDER_KEYWORDS = [
    "define a squad",            # 1. Choose squad
    "create release branch",     # 2. Branch creation
    "deliver",                   # 3. Deliver RC1 (blocked by branch)
    "test plan",                 # 4. Test plan tasks
    "test he in production",     # 5. Test staging (blocked by RC1)
    "close the release",         # 6. Close release
]


def _release_sort_key(item: dict) -> tuple:
    """Return a sort key that places known release cards in dependency order."""
    summary_lower = item["summary"].lower()
    for idx, keyword in enumerate(_RELEASE_ORDER_KEYWORDS):
        if keyword in summary_lower:
            return (idx, item["_start"], item["_end"])
    # Unknown cards: after all known ones, sorted by date
    return (len(_RELEASE_ORDER_KEYWORDS), item["_start"], item["_end"])


def _build_timeline_html(epic: dict, children: list[dict], jira_url: str) -> str:
    """
    Build a Gantt-style visual timeline for one release.
    Each child is a horizontal bar from Development → Done (or today if not done).
    """
    today = datetime.now()
    items = []
    for c in children:
        start = _parse_date(c["start_date"])
        end = _parse_date(c["done_date"]) or today
        if start is None:
            continue
        if end < start:
            end = start
        items.append({**c, "_start": start, "_end": end})

    if not items:
        return '<p class="meta"><em>No timeline data (no dates available).</em></p>'

    # Compute global range
    min_date = min(i["_start"] for i in items)
    max_date = max(i["_end"] for i in items)
    span_days = max((max_date - min_date).days, 1)

    # Build date axis labels (one per week, at most ~20 labels)
    from datetime import timedelta
    step = max(span_days // 16, 1)
    axis_labels = []
    d = min_date
    while d <= max_date:
        pct = (d - min_date).days / span_days * 100
        axis_labels.append((pct, d.strftime("%b %d")))
        d += timedelta(days=step)

    lines: list[str] = []
    lines.append('<div class="timeline-container">')

    # Axis
    lines.append('<div class="timeline-axis">')
    for pct, label in axis_labels:
        lines.append(
            f'<span class="axis-label" style="left:{pct:.1f}%">{label}</span>'
        )
    lines.append('</div>')

    # Bars
    for item in items:
        left = (item["_start"] - min_date).days / span_days * 100
        width = max((item["_end"] - item["_start"]).days / span_days * 100, 0.5)
        # Declined cards stay grey regardless of due date
        if item["status"].lower() == "declined":
            color = "#90A4AE"                        # declined → blue-grey
            color_key = "grey"
        else:
            due_dt_for_color = _parse_date(item.get("due_date"))
            if due_dt_for_color is None:
                color = "#27AE60"                        # no due date → emerald green
                color_key = "green"
            elif (item["_end"] - due_dt_for_color).days > 8 or (item["_start"] - due_dt_for_color).days > 8:
                color = "#C0392B"                        # start or end >8 days after due date → crimson
                color_key = "red"
            elif (item["_start"] - due_dt_for_color).days > 1:
                color = "#F07509"                        # started >1 day after due date → orange
                color_key = "orange"
            elif item["_end"] > due_dt_for_color:
                color = "#FAD335"                        # ends after due date → yellow
                color_key = "yellow"
            else:
                color = "#27AE60"                        # on time → emerald green
                color_key = "green"
        is_open = item["done_date"] is None
        bar_class = "timeline-bar open" if is_open else "timeline-bar"
        assignee = _esc(item.get("assignee") or "Unassigned")
        due_date_str = item.get("due_date")
        due_marker_html = ""
        if due_date_str:
            due_dt = _parse_date(due_date_str)
            if due_dt is not None:
                due_pct = (due_dt - min_date).days / span_days * 100
                due_pct = max(0.0, min(100.0, due_pct))
                due_marker_html = (
                    f'<div class="due-date-marker" '
                    f'style="left:{due_pct:.2f}%" '
                    f'title="Due: {_fmt_date(due_date_str)}"></div>'
                )
        tooltip = (
            f'{_esc(item["key"])} — {_esc(item["summary"])}\n'
            f'Status: {_esc(item["status"])}  |  {_esc(item.get("priority",""))}\n'
            f'Development: {_fmt_date(item["start_date"])}  →  '
            f'Done: {_fmt_date(item["done_date"])}\n'
            + (f'Due: {_fmt_date(due_date_str)}\n' if due_date_str else "")
            + f'Assignee: {assignee}'
        )
        label_text = f'{_esc(item["key"])} {_esc(item["summary"][:50])}'
        card_url = f'{jira_url}/browse/{_esc(item["key"])}'
        lines.append(
            f'<div class="timeline-row" data-color-key="{color_key}">'
            f'<div class="timeline-label" title="{tooltip}">'
            f'<a href="{card_url}" target="_blank" class="card-link">{label_text}</a></div>'
            f'<div class="timeline-track">'
            f'{due_marker_html}'
            f'<div class="{bar_class}" '
            f'style="left:{left:.2f}%;width:{width:.2f}%;background:{color}" '
            f'title="{tooltip}">'
            f'<span class="bar-dates">{(item["_end"] - item["_start"]).days}d'
            f'</span></div></div></div>'
        )

    lines.append('</div>')  # timeline-container
    return "\n".join(lines)


def build_html(releases: list[tuple[dict, list[dict]]], jira_url: str) -> str:
    """Return a full HTML page with release timelines."""
    parts: list[str] = []
    parts.append(
        """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jira Release Timelines</title>
<style>
  body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 2rem; background: #f5f5f5; }
  h1 { color: #1a237e; }
  .release { background: #fff; border-radius: 8px; padding: 1.2rem 1.5rem;
             margin-bottom: 1.5rem; box-shadow: 0 2px 6px rgba(0,0,0,.1); }
  .release h2 { margin: 0 0 .3rem; font-size: 1.25rem; }
  .release .meta { color: #666; font-size: .85rem; margin-bottom: .8rem; }
  .progress-bar { background: #e0e0e0; border-radius: 6px; height: 14px;
                  overflow: hidden; max-width: 400px; margin-bottom: .8rem; }
  .progress-fill { height: 100%; border-radius: 6px; }
  table { border-collapse: collapse; width: 100%; font-size: .88rem; }
  th { background: #e8eaf6; text-align: left; padding: 6px 10px; }
  td { padding: 6px 10px; border-bottom: 1px solid #eee; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
           color: #fff; font-size: .78rem; font-weight: 600; }
  .toc a { text-decoration: none; color: #1a237e; }
  .toc a:hover { text-decoration: underline; }
  .toc { margin-bottom: 2rem; }

  /* ── Timeline (Gantt) styles ─────────────────── */
  .timeline-container { margin: 1.2rem 0 .5rem; position: relative; }
  .timeline-axis { position: relative; height: 22px; border-bottom: 1px solid #ccc;
                   margin-left: 320px; margin-bottom: 4px; }
  .axis-label { position: absolute; top: 0; font-size: .7rem; color: #888;
                transform: translateX(-50%); white-space: nowrap; }
  .timeline-row { display: flex; align-items: center; margin-bottom: 3px; min-height: 28px; }
  .timeline-label { width: 320px; flex-shrink: 0; font-size: .78rem; color: #333;
                    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
                    padding-right: 8px; cursor: default; }
  .timeline-track { flex: 1; position: relative; height: 22px;
                    background: repeating-linear-gradient(
                      90deg, #f0f0f0 0px, #f0f0f0 1px, transparent 1px, transparent 50px
                    ); border-radius: 3px; }
  .timeline-bar { position: absolute; top: 2px; height: 18px; border-radius: 4px;
                  min-width: 4px; cursor: pointer; opacity: .9;
                  transition: opacity .15s; display: flex; align-items: center;
                  overflow: hidden; }
  .timeline-bar:hover { opacity: 1; box-shadow: 0 1px 6px rgba(0,0,0,.25); z-index: 2; }
  .timeline-bar.open { background-image: repeating-linear-gradient(
      -45deg, transparent, transparent 4px, rgba(255,255,255,.25) 4px,
      rgba(255,255,255,.25) 8px) !important; }
  .bar-dates { font-size: .65rem; color: #fff; padding: 0 6px; white-space: nowrap;
               text-shadow: 0 1px 2px rgba(0,0,0,.4); }
  .due-date-marker { position: absolute; top: 0; bottom: 0; width: 2px;
                     background: #C0392B; z-index: 3; pointer-events: none;
                     box-shadow: 0 0 3px rgba(192,57,43,.6); }
  .card-link { text-decoration: none; color: #1a237e; }
  .card-link:hover { text-decoration: underline; }
  h3.timeline-heading { margin: 1.4rem 0 .3rem; color: #37474f; font-size: 1rem; }
  .legend { display: flex; flex-wrap: wrap; gap: .6rem 1.4rem; align-items: center;
            background: #fff; border-radius: 8px; padding: .7rem 1.2rem;
            margin-bottom: 1.5rem; box-shadow: 0 2px 6px rgba(0,0,0,.1);
            font-size: .83rem; color: #333; }
  .legend-title { font-weight: 600; margin-right: .4rem; color: #37474f; }
  .legend-item { display: flex; align-items: center; gap: .4rem; }
  .legend-swatch { display: inline-block; width: 18px; height: 18px;
                   border-radius: 3px; flex-shrink: 0; }
  .legend-filter { display: flex; align-items: center; gap: .4rem; cursor: pointer;
                   border: 2px solid transparent; border-radius: 6px; padding: 3px 8px;
                   background: none; font-size: .83rem; color: #333; font-family: inherit;
                   transition: opacity .2s, border-color .2s; }
  .legend-filter.inactive { opacity: .35; border-color: #bbb; text-decoration: line-through; }
  .legend-filter:hover { border-color: #999; }
  .legend-marker { display: inline-block; width: 3px; height: 18px;
                   background: #C0392B; border-radius: 1px; flex-shrink: 0;
                   box-shadow: 0 0 3px rgba(192,57,43,.6); }
</style></head><body>
<h1>Jira Release Timelines</h1>
<p style="color:#666">Generated on """
        + datetime.now().strftime("%Y-%m-%d %H:%M")
        + """</p>
"""
    )

    # Table of contents
    parts.append('<div class="toc"><h3>Releases</h3><ol>')
    for epic, children in releases:
        done = sum(1 for c in children if c["status"].upper() == "DONE")
        total = len(children)
        parts.append(
            f'<li><a href="#{_esc(epic["key"])}">{_esc(epic["summary"])}</a>'
            f" — {epic['status']} ({done}/{total})</li>"
        )
    parts.append("</ol></div>")
    parts.append(
        '<div class="legend">'
        '<span class="legend-title">Bar colour (click to filter):</span>'
        '<button class="legend-filter" data-filter="green"><span class="legend-swatch" style="background:#27AE60"></span>On time or no due date</button>'
        '<button class="legend-filter" data-filter="yellow"><span class="legend-swatch" style="background:#FAD335"></span>Ends after due date</button>'
        '<button class="legend-filter" data-filter="orange"><span class="legend-swatch" style="background:#F07509"></span>Started after due date</button>'
        '<button class="legend-filter" data-filter="red"><span class="legend-swatch" style="background:#C0392B"></span>Late &gt;8 days</button>'
        '<button class="legend-filter" data-filter="grey"><span class="legend-swatch" style="background:#90A4AE"></span>Declined</button>'
        '<span class="legend-item"><span class="legend-marker"></span>Due date</span>'
        '</div>'
    )

    # Each release
    for epic, children in releases:
        color = _STATUS_COLORS.get(epic["status"], "#9E9E9E")
        done = sum(1 for c in children if c["status"].upper() == "DONE")
        total = len(children)
        pct = int(done / total * 100) if total else 0

        parts.append(f'<div class="release" id="{_esc(epic["key"])}">')
        epic_url = f'{jira_url}/browse/{_esc(epic["key"])}'

        # Compute total span: first dev start → last done
        span_text = ""
        if children:
            starts = [_parse_date(c["start_date"]) for c in children if _parse_date(c["start_date"])]
            ends = [_parse_date(c["done_date"]) for c in children if _parse_date(c["done_date"])]
            if starts and ends:
                first_start = min(starts)
                last_end = max(ends)
                total_days = (last_end - first_start).days
                span_text = (
                    f' <span style="font-size:.85rem;color:#555;font-weight:normal">'
                    f'— {total_days} days '
                    f'({first_start.strftime("%b %d")} → {last_end.strftime("%b %d")})</span>'
                )

        parts.append(
            f'<h2><a href="{epic_url}" target="_blank" class="card-link">'
            f'{_esc(epic["summary"])}</a> '
            f'<span class="badge" style="background:{color}">{_esc(epic["status"])}</span>'
            f'{span_text}</h2>'
        )
        parts.append(
            f'<div class="meta">{_esc(epic["key"])} · '
            f"Created {_fmt_date(epic['created'])} · "
            f"Updated {_fmt_date(epic['updated'])}</div>"
        )

        # Progress bar
        parts.append(
            f'<div class="progress-bar">'
            f'<div class="progress-fill" style="width:{pct}%;background:{color}"></div>'
            f"</div>"
        )
        parts.append(
            f'<div class="meta">{pct}% complete ({done}/{total} items)</div>'
        )

        # ── Visual timeline (Gantt chart) ──
        if children:
            parts.append('<h3 class="timeline-heading">Timeline</h3>')
            parts.append(_build_timeline_html(epic, children, jira_url))
        else:
            parts.append("<p><em>No child items found.</em></p>")

        parts.append("</div>")

    parts.append("""<script>
(function(){
  var active={};
  document.querySelectorAll('.legend-filter[data-filter]').forEach(function(btn){
    active[btn.dataset.filter]=true;
    btn.addEventListener('click',function(){
      var k=btn.dataset.filter;
      active[k]=!active[k];
      btn.classList.toggle('inactive',!active[k]);
      document.querySelectorAll('.timeline-row[data-color-key="'+k+'"]').forEach(function(row){
        row.style.display=active[k]?'':'none';
      });
    });
  });
})();
</script>""")
    parts.append("</body></html>")
    return "\n".join(parts)


# ── Main ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Jira release epics and display child-item timelines."
    )
    parser.add_argument(
        "--search",
        default="HE CORE release",
        help='Text to search in epic summaries (default: "HE CORE release")',
    )
    parser.add_argument(
        "--year",
        default=None,
        help='Filter releases by year, e.g. "2026"',
    )
    parser.add_argument(
        "--release",
        default=None,
        help='Filter to a specific release version, e.g. "2026.3.0"',
    )
    parser.add_argument(
        "--output",
        choices=["console", "html"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "--html-file",
        default="release_timelines.html",
        help="Output HTML file path (default: release_timelines.html)",
    )
    parser.add_argument(
        "--config",
        default="config.ini",
        help="Path to config.ini (default: config.ini)",
    )
    args = parser.parse_args()

    jira = connect_jira(args.config)

    # Read Jira URL for card links
    config = configparser.ConfigParser()
    config.read(args.config)
    jira_url = config["jira"]["url"].rstrip("/")

    # 1. Fetch release epics
    epics = fetch_release_epics(
        jira, args.search, year=args.year, release=args.release
    )
    if not epics:
        print("No release epics found.")
        return

    # Sort by version number descending
    epics.sort(key=lambda e: extract_version(e["summary"]), reverse=True)

    # 2. For each epic, fetch children
    releases: list[tuple[dict, list[dict]]] = []
    for epic in epics:
        print(f"  Fetching children for {epic['key']} – {epic['summary']} …")
        children = fetch_children(jira, epic["key"])
        releases.append((epic, children))

    # 3. Render
    if args.output == "html":
        html = build_html(releases, jira_url)
        out = Path(args.html_file)
        out.write_text(html, encoding="utf-8")
        print(f"\nHTML report written to {out.resolve()}")
    else:
        for epic, children in releases:
            print_timeline(epic, children)

    print(f"\nTotal: {len(releases)} release(s) processed.")


if __name__ == "__main__":
    main()
