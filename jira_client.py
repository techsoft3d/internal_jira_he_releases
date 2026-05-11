import sys

import configparser
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
