"""Tests for jira_client.connect_jira()."""

import configparser
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jira_client import connect_jira


# ── Helpers ────────────────────────────────────────────────────────────


def _make_config(tmp_path: Path, **overrides) -> Path:
    section = {
        "url": "https://example.atlassian.net",
        "username": "user@example.com",
        "api_token": "secret",
        **overrides,
    }
    cfg = configparser.ConfigParser()
    cfg["jira"] = section
    p = tmp_path / "config.ini"
    import io
    buf = io.StringIO()
    cfg.write(buf)
    p.write_text(buf.getvalue())
    return p


# ── Tests ──────────────────────────────────────────────────────────────


def test_missing_config_exits(tmp_path):
    """connect_jira() must call sys.exit when the config file is absent."""
    with pytest.raises(SystemExit):
        connect_jira(str(tmp_path / "nonexistent.ini"))


def test_returns_jira_instance(tmp_path):
    """connect_jira() must return the JIRA object produced by the constructor."""
    config_path = _make_config(tmp_path)
    mock_jira = MagicMock()

    with patch("jira_client.JIRA", return_value=mock_jira) as mock_cls:
        result = connect_jira(str(config_path))

    assert result is mock_jira


def test_jira_constructor_receives_correct_args(tmp_path):
    """JIRA must be called with the URL and credentials from config.ini."""
    config_path = _make_config(
        tmp_path,
        url="https://myorg.atlassian.net",
        username="admin@myorg.com",
        api_token="tok123",
    )

    with patch("jira_client.JIRA", return_value=MagicMock()) as mock_cls:
        connect_jira(str(config_path))

    mock_cls.assert_called_once_with(
        options={"server": "https://myorg.atlassian.net", "rest_api_version": "3"},
        basic_auth=("admin@myorg.com", "tok123"),
    )


def test_trailing_slash_preserved(tmp_path):
    """URL is passed as-is (stripping is the caller's responsibility)."""
    config_path = _make_config(tmp_path, url="https://example.atlassian.net/")

    with patch("jira_client.JIRA", return_value=MagicMock()) as mock_cls:
        connect_jira(str(config_path))

    called_url = mock_cls.call_args.kwargs["options"]["server"]
    assert called_url == "https://example.atlassian.net/"
