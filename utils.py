import re
from datetime import datetime
from typing import Optional, Tuple


def extract_version(summary: str) -> Tuple[int, ...]:
    """
    Pull the version tuple from a summary like '[2026.3.0] HE Core ...'.
    Returns e.g. (2026, 3, 0).  Falls back to (0,) if not found.
    """
    m = re.search(r"\[(\d+(?:\.\d+)+)\]", summary)
    if m:
        return tuple(int(x) for x in m.group(1).split("."))
    return (0,)


def fmt_date(iso: Optional[str]) -> str:
    """Format an ISO date string as YYYY-MM-DD, or '—' if absent/unparseable."""
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(iso)[:10]


def parse_date(iso: Optional[str]) -> Optional[datetime]:
    """Parse an ISO date string to a naive datetime, or None."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def esc(text: Optional[str]) -> str:
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
