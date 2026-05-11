"""Tests for models.py — Epic and ChildIssue dataclasses."""

import pytest

from models import ChildIssue, Epic


# ── 2025 golden snapshot ───────────────────────────────────────────────
# Source: Jira TOC screenshot (May 2026)

EXPECTED_2025_EPICS = [
    ("[2025.9.0] HE Core Release Activities",    "Done"),
    ("[2025.9.0] HE/HP Core Release Activities", "Declined"),
    ("[2025.8.0] HE/HP Core Release Activities", "Done"),
    ("[2025.7.0] HE/HP Core Release Activities", "Done"),
    ("[2025.6.0] HE/HP Core Release Activities", "Done"),
    ("[2025.5.0] HE/HP Core Release Activities", "Done"),
    ("[2025.4.0] HE/HP Core Release Activities", "Done"),
    ("[2025.3.0] HE/HP Core Release Activities", "Done"),
    ("[2025.2.0] HE/HP Core Release Activities", "Done"),
    ("[2025.1.0] HE/HP Core Release Activities", "Done"),
]

# ── HE-16485 children snapshot ─────────────────────────────────────────
# Source: [2025.8.0] HE/HP Core Release Activities timeline screenshot
# 90% complete (9/10 items), 54 days Oct 02 → Nov 26

HE16485_EPIC = Epic(
    key="HE-16485",
    summary="[2025.8.0] HE/HP Core Release Activities",
    status="Done",
    created="2025-10-02T00:00:00+00:00",
    updated="2026-01-06T00:00:00+00:00",
)

HE16485_CHILDREN = [
    ChildIssue(key="HE-16486", summary="[Release] Define a squad for the HE release process",    status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16487", summary="[Release] Deliver HE/HED RC 1",                          status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16488", summary="[Release] Create release branch ready to stabilise",     status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16489", summary="[Release] Test HE in production environment",            status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16490", summary="[Release] HE Close the release",                         status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16491", summary="[Release] HE/HED Test Plan on Release branch",           status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16492", summary="[Release] HE/HP/HED Test Plan on Release branch",        status="In Progress",created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16493", summary="[Release] HE/HP/HED Test Plan on Release branch (copy)", status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16609", summary="[Release] Remove the deprecated HP documentation",       status="Done",       created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
    ChildIssue(key="HE-16642", summary="[Release] [USD] Deliver Experimental USD writing support",status="Done",      created="2025-10-02T00:00:00+00:00", updated="2025-10-02T00:00:00+00:00"),
]


class TestEpic:
    def test_required_fields(self):
        epic = Epic(
            key="HE-1",
            summary="[2026.3.0] HE CORE release",
            status="In Progress",
            created="2026-01-10T08:00:00+00:00",
            updated="2026-03-01T12:00:00+00:00",
        )
        assert epic.key == "HE-1"
        assert epic.summary == "[2026.3.0] HE CORE release"
        assert epic.status == "In Progress"
        assert epic.created == "2026-01-10T08:00:00+00:00"
        assert epic.updated == "2026-03-01T12:00:00+00:00"


class TestChildIssue:
    def test_required_fields_only(self):
        child = ChildIssue(
            key="HE-42",
            summary="Set up CI pipeline",
            status="Done",
            created="2026-01-15T09:00:00+00:00",
            updated="2026-02-01T17:00:00+00:00",
        )
        assert child.key == "HE-42"
        assert child.status == "Done"

    def test_optional_fields_default_to_none(self):
        child = ChildIssue(
            key="HE-42",
            summary="Set up CI pipeline",
            status="To Do",
            created="2026-01-15T09:00:00+00:00",
            updated="2026-01-15T09:00:00+00:00",
        )
        assert child.type is None
        assert child.priority is None
        assert child.assignee is None
        assert child.story_points is None
        assert child.start_date is None
        assert child.done_date is None
        assert child.due_date is None
        assert child.resolution_date is None

    def test_all_fields(self):
        child = ChildIssue(
            key="HE-99",
            summary="Write release notes",
            status="Done",
            created="2026-02-01T08:00:00+00:00",
            updated="2026-03-15T10:00:00+00:00",
            type="Task",
            priority="High",
            assignee="Alice Dupont",
            story_points=3.0,
            start_date="2026-02-05T08:00:00+00:00",
            done_date="2026-03-10T17:00:00+00:00",
            due_date="2026-03-08",
            resolution_date="2026-03-10T17:00:00+00:00",
        )
        assert child.type == "Task"
        assert child.priority == "High"
        assert child.assignee == "Alice Dupont"
        assert child.story_points == 3.0
        assert child.done_date == "2026-03-10T17:00:00+00:00"
        assert child.due_date == "2026-03-08"


class TestEpic2025Snapshot:
    """Golden-snapshot test: the 10 expected 2025 release epics."""

    def _make_epics(self):
        return [
            Epic(key=f"HE-{i}", summary=summary, status=status,
                 created="2025-01-01T00:00:00+00:00",
                 updated="2025-01-01T00:00:00+00:00")
            for i, (summary, status) in enumerate(EXPECTED_2025_EPICS, start=1)
        ]

    def test_count(self):
        assert len(self._make_epics()) == 10

    def test_all_summaries_contain_2025(self):
        for epic in self._make_epics():
            assert "[2025." in epic.summary, f"Missing year tag: {epic.summary}"

    def test_statuses(self):
        epics = self._make_epics()
        statuses = {e.summary: e.status for e in epics}
        assert statuses["[2025.9.0] HE Core Release Activities"] == "Done"
        assert statuses["[2025.9.0] HE/HP Core Release Activities"] == "Declined"
        # All others are Done
        for summary, status in EXPECTED_2025_EPICS:
            if summary != "[2025.9.0] HE/HP Core Release Activities":
                assert status == "Done", f"Expected Done for {summary}, got {status}"

    @pytest.mark.parametrize("summary,status", EXPECTED_2025_EPICS)
    def test_each_epic_is_valid(self, summary, status):
        epic = Epic(key="HE-X", summary=summary, status=status,
                    created="2025-01-01T00:00:00+00:00",
                    updated="2025-01-01T00:00:00+00:00")
        assert epic.summary == summary
        assert epic.status == status


class TestHE16485Children:
    """Golden-snapshot test for the 10 children of HE-16485 ([2025.8.0])."""

    def test_epic_key_and_status(self):
        assert HE16485_EPIC.key == "HE-16485"
        assert HE16485_EPIC.status == "Done"

    def test_child_count(self):
        assert len(HE16485_CHILDREN) == 10

    def test_progress_nine_of_ten_done(self):
        done = sum(1 for c in HE16485_CHILDREN if c.status == "Done")
        assert done == 9

    def test_one_in_progress(self):
        not_done = [c for c in HE16485_CHILDREN if c.status != "Done"]
        assert len(not_done) == 1
        assert not_done[0].key == "HE-16492"

    def test_all_keys_sequential(self):
        keys = [c.key for c in HE16485_CHILDREN]
        assert keys == [
            "HE-16486", "HE-16487", "HE-16488", "HE-16489", "HE-16490",
            "HE-16491", "HE-16492", "HE-16493", "HE-16609", "HE-16642",
        ]

    @pytest.mark.parametrize("child", HE16485_CHILDREN)
    def test_each_child_summary_starts_with_release(self, child):
        assert child.summary.startswith("[Release]"), (
            f"{child.key} summary does not start with [Release]: {child.summary}"
        )
