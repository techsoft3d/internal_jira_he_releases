"""Tests for jira_fetch.py — all Jira calls are mocked."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from jira_fetch import _find_status_date, fetch_children, fetch_release_epics
from models import ChildIssue, Epic


# ── Helpers ────────────────────────────────────────────────────────────


def _make_status(name):
    s = MagicMock()
    s.name = name
    return s


def _make_raw_epic(key, summary, status, created, updated):
    e = MagicMock()
    e.key = key
    e.fields.summary = summary
    e.fields.status = _make_status(status)
    e.fields.created = created
    e.fields.updated = updated
    return e


def _make_changelog_item(field, toString):
    item = MagicMock()
    item.field = field
    item.toString = toString
    return item


def _make_history(created, items):
    hist = MagicMock()
    hist.created = created
    hist.items = items
    return hist


def _make_raw_child(
    key, summary, status="To Do", created="2026-01-01T00:00:00+00:00",
    updated="2026-01-01T00:00:00+00:00", assignee_name=None, priority_name=None,
    issue_type="Task", story_points=None, resolutiondate=None, duedate=None,
    changelog_histories=None,
):
    c = MagicMock()
    c.key = key
    f = c.fields
    f.summary = summary
    f.status = _make_status(status)
    f.created = created
    f.updated = updated
    f.resolutiondate = resolutiondate
    f.duedate = duedate
    f.story_points = story_points
    f.customfield_10016 = None

    f.assignee = None
    if assignee_name:
        f.assignee = MagicMock()
        f.assignee.displayName = assignee_name

    f.priority = None
    if priority_name:
        f.priority = MagicMock()
        f.priority.name = priority_name

    f.issuetype = MagicMock()
    f.issuetype.name = issue_type

    c.changelog.histories = changelog_histories or []
    return c


# ── _find_status_date ──────────────────────────────────────────────────


class TestFindStatusDate:
    def test_finds_matching_status(self):
        histories = [
            _make_history("2026-02-01T10:00:00+00:00", [
                _make_changelog_item("status", "Development"),
            ])
        ]
        assert _find_status_date(histories, "Development") == "2026-02-01T10:00:00+00:00"

    def test_case_insensitive(self):
        histories = [
            _make_history("2026-02-01T10:00:00+00:00", [
                _make_changelog_item("status", "DONE"),
            ])
        ]
        assert _find_status_date(histories, "done") == "2026-02-01T10:00:00+00:00"

    def test_returns_none_when_not_found(self):
        histories = [
            _make_history("2026-02-01T10:00:00+00:00", [
                _make_changelog_item("status", "In Progress"),
            ])
        ]
        assert _find_status_date(histories, "Done") is None

    def test_returns_none_for_empty_changelog(self):
        assert _find_status_date([], "Done") is None

    def test_returns_first_match(self):
        histories = [
            _make_history("2026-02-01T00:00:00+00:00", [_make_changelog_item("status", "Done")]),
            _make_history("2026-03-01T00:00:00+00:00", [_make_changelog_item("status", "Done")]),
        ]
        assert _find_status_date(histories, "Done") == "2026-02-01T00:00:00+00:00"

    def test_ignores_non_status_fields(self):
        histories = [
            _make_history("2026-02-01T00:00:00+00:00", [
                _make_changelog_item("assignee", "Done"),
            ])
        ]
        assert _find_status_date(histories, "Done") is None


# ── fetch_release_epics ────────────────────────────────────────────────


class TestFetchReleaseEpics:
    def _jira_with(self, epics_raw):
        jira = MagicMock()
        jira.search_issues.return_value = epics_raw
        return jira

    def test_returns_epic_models(self):
        raw = [_make_raw_epic("HE-1", "[2026.3.0] HE Core release", "In Progress",
                               "2026-01-01T00:00:00+00:00", "2026-03-01T00:00:00+00:00")]
        result = fetch_release_epics(self._jira_with(raw), "HE CORE release")
        assert len(result) == 1
        assert isinstance(result[0], Epic)
        assert result[0].key == "HE-1"
        assert result[0].status == "In Progress"

    def test_filter_by_release(self):
        raw = [
            _make_raw_epic("HE-1", "[2026.3.0] HE Core release", "Done", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
            _make_raw_epic("HE-2", "[2026.4.0] HE Core release", "Done", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        ]
        result = fetch_release_epics(self._jira_with(raw), "HE CORE release", release="2026.3.0")
        assert len(result) == 1
        assert result[0].key == "HE-1"

    def test_filter_by_year(self):
        raw = [
            _make_raw_epic("HE-1", "[2026.3.0] HE Core release", "Done", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
            _make_raw_epic("HE-2", "[2025.9.0] HE Core release", "Done", "2025-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00"),
        ]
        result = fetch_release_epics(self._jira_with(raw), "HE CORE release", year="2025")
        assert len(result) == 1
        assert result[0].key == "HE-2"

    def test_release_filter_takes_priority_over_year(self):
        raw = [
            _make_raw_epic("HE-1", "[2026.3.0] HE Core release", "Done", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
            _make_raw_epic("HE-2", "[2026.4.0] HE Core release", "Done", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        ]
        result = fetch_release_epics(self._jira_with(raw), "HE CORE", year="2026", release="2026.3.0")
        assert len(result) == 1
        assert result[0].key == "HE-1"

    def test_no_match_returns_empty(self):
        raw = [_make_raw_epic("HE-1", "[2026.3.0] HE Core release", "Done", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00")]
        result = fetch_release_epics(self._jira_with(raw), "HE CORE release", release="9999.0.0")
        assert result == []


# ── fetch_children ─────────────────────────────────────────────────────


class TestFetchChildren:
    def _jira_with(self, children_raw):
        jira = MagicMock()
        jira.search_issues.return_value = children_raw
        return jira

    def test_returns_child_issue_models(self):
        raw = [_make_raw_child("HE-42", "Do the thing")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert len(result) == 1
        assert isinstance(result[0], ChildIssue)
        assert result[0].key == "HE-42"

    def test_start_date_from_development_changelog(self):
        histories = [
            _make_history("2026-02-10T08:00:00+00:00", [
                _make_changelog_item("status", "Development"),
            ])
        ]
        raw = [_make_raw_child("HE-42", "Task", changelog_histories=histories,
                                created="2026-01-01T00:00:00+00:00")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].start_date == "2026-02-10T08:00:00+00:00"

    def test_start_date_fallback_to_created(self):
        raw = [_make_raw_child("HE-42", "Task", created="2026-01-15T09:00:00+00:00")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].start_date == "2026-01-15T09:00:00+00:00"

    def test_done_date_from_changelog(self):
        histories = [
            _make_history("2026-03-01T17:00:00+00:00", [
                _make_changelog_item("status", "Done"),
            ])
        ]
        raw = [_make_raw_child("HE-42", "Task", changelog_histories=histories)]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].done_date == "2026-03-01T17:00:00+00:00"

    def test_done_date_fallback_to_resolutiondate(self):
        raw = [_make_raw_child("HE-42", "Task", resolutiondate="2026-03-05T00:00:00+00:00")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].done_date == "2026-03-05T00:00:00+00:00"

    def test_done_date_none_when_not_resolved(self):
        raw = [_make_raw_child("HE-42", "Task")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].done_date is None

    def test_assignee_display_name(self):
        raw = [_make_raw_child("HE-42", "Task", assignee_name="Alice Dupont")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].assignee == "Alice Dupont"

    def test_no_assignee(self):
        raw = [_make_raw_child("HE-42", "Task")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].assignee is None

    def test_story_points(self):
        raw = [_make_raw_child("HE-42", "Task", story_points=5.0)]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].story_points == 5.0

    def test_due_date(self):
        raw = [_make_raw_child("HE-42", "Task", duedate="2026-03-08")]
        result = fetch_children(self._jira_with(raw), "HE-1")
        assert result[0].due_date == "2026-03-08"

    def test_empty_epic_returns_empty_list(self):
        result = fetch_children(self._jira_with([]), "HE-1")
        assert result == []
