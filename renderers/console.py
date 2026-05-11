from typing import Dict, List

from models import ChildIssue, Epic
from utils import fmt_date


STATUS_SYMBOLS: Dict[str, str] = {
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


def print_timeline(epic: Epic, children: List[ChildIssue]) -> None:
    """Print a text-based timeline for one release."""
    print()
    print("=" * 80)
    sym = STATUS_SYMBOLS.get(epic.status, "⬜")
    print(f" {sym}  {epic.summary}  ({epic.key})  —  {epic.status}")
    print(f"     Created: {fmt_date(epic.created)}   Updated: {fmt_date(epic.updated)}")
    print("-" * 80)

    if not children:
        print("     (no child work items)")
        print("=" * 80)
        return

    done = sum(1 for c in children if c.status.upper() == "DONE")
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
        sym = STATUS_SYMBOLS.get(c.status, "⬜")
        sp = str(c.story_points) if c.story_points else "—"
        assignee = c.assignee or "Unassigned"
        if len(assignee) > 14:
            assignee = assignee[:12] + ".."
        issue_type = c.type or ""
        if len(issue_type) > 10:
            issue_type = issue_type[:10] + ".."
        print(
            f"  {c.key:<12} {issue_type:<12} {sym} {c.status:<18} "
            f"{(c.priority or '—'):<10} {sp:>3}  "
            f"{fmt_date(c.start_date):<12} {fmt_date(c.done_date):<12} "
            f"{assignee}"
        )

    print("=" * 80)
