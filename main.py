"""
CLI entry point: Fetch Jira release epics and display child-item timelines.

Usage:
    python main.py --output console --release 2026.3.0
    python main.py --year 2026
    python main.py --output html --year 2025
"""

import argparse
import configparser
from pathlib import Path
from typing import List, Tuple

from jira_client import connect_jira
from jira_fetch import fetch_children, fetch_release_epics
from models import ChildIssue, Epic
from renderers.console import print_timeline
from utils import extract_version


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Jira release epics and display child-item timelines."
    )
    parser.add_argument(
        "--search", default="HE CORE release",
        help='Text to search in epic summaries (default: "HE CORE release")',
    )
    parser.add_argument("--year", default=None, help='Filter by year, e.g. "2026"')
    parser.add_argument("--release", default=None, help='Filter to a specific version, e.g. "2026.3.0"')
    parser.add_argument(
        "--output", choices=["console", "html"], default="console",
        help="Output format (default: console)",
    )
    parser.add_argument("--html-file", default="release_timelines.html", help="Output HTML file path")
    parser.add_argument("--config", default="config.ini", help="Path to config.ini")
    args = parser.parse_args()

    jira = connect_jira(args.config)

    config = configparser.ConfigParser()
    config.read(args.config)
    jira_url = config["jira"]["url"].rstrip("/")

    # 1. Fetch release epics
    epics = fetch_release_epics(jira, args.search, year=args.year, release=args.release)
    if not epics:
        print("No release epics found.")
        return

    epics.sort(key=lambda e: extract_version(e.summary), reverse=True)

    # 2. For each epic, fetch children
    releases: List[Tuple[Epic, List[ChildIssue]]] = []
    for epic in epics:
        print(f"  Fetching children for {epic.key} – {epic.summary} …")
        children = fetch_children(jira, epic.key)
        releases.append((epic, children))

    # 3. Render
    if args.output == "html":
        # TODO: wire up HTML renderer (Commit 8)
        print("HTML output not yet implemented.")
    else:
        for epic, children in releases:
            print_timeline(epic, children)

    print(f"\nTotal: {len(releases)} release(s) processed.")


if __name__ == "__main__":
    main()
