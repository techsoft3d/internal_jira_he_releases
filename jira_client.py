import sys

import configparser
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

from jira import JIRA
from jira.resources import Issue

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


# ── Search (replaces jira.search_issues, which calls the removed /search endpoint) ──


def search_jql(
    jira: JIRA,
    jql: str,
    fields: Optional[str] = None,
    max_results: int = 100,
) -> List[Issue]:
    """
    Call POST /rest/api/3/search/jql (the replacement for the removed GET /search).
    Returns a list of jira.resources.Issue objects identical to what search_issues() returned.
    Note: expand is not supported by this endpoint — use fetch_changelog() separately.
    """
    url = f"{jira._options['server']}/rest/api/3/search/jql"

    payload: dict = {"jql": jql, "maxResults": max_results}
    if fields:
        payload["fields"] = [f.strip() for f in fields.split(",")]

    assert jira._session is not None, "Jira session is not initialised"
    response = jira._session.post(url, json=payload)
    response.raise_for_status()

    session = jira._session
    return [
        Issue(jira._options, session, raw=item)
        for item in response.json().get("issues", [])
    ]


def fetch_changelog(jira: JIRA, issue_key: str) -> list:
    """
    Fetch the full changelog for one issue via GET /rest/api/3/issue/{key}/changelog.
    Returns a list of history objects with .created and .items attributes,
    identical in shape to what expand=changelog used to provide.
    """
    assert jira._session is not None, "Jira session is not initialised"
    url = f"{jira._options['server']}/rest/api/3/issue/{issue_key}/changelog"
    histories: list = []
    start_at = 0
    while True:
        response = jira._session.get(url, params={"startAt": start_at, "maxResults": 100})
        response.raise_for_status()
        data = response.json()
        for raw_hist in data.get("values", []):
            hist = SimpleNamespace(
                created=raw_hist.get("created", ""),
                items=[
                    SimpleNamespace(
                        field=raw_item.get("field"),
                        toString=raw_item.get("toString"),
                    )
                    for raw_item in raw_hist.get("items", [])
                ],
            )
            histories.append(hist)
        if data.get("isLast", True) or len(histories) >= data.get("total", 0):
            break
        start_at += len(data.get("values", []))
    return histories
