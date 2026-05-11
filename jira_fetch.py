from typing import List, Optional, cast

from jira import JIRA, Issue

from models import ChildIssue, Epic


def _find_status_date(changelog_histories, target_status: str) -> Optional[str]:
    """
    Walk the changelog and return the ISO timestamp of the first transition
    whose *to* status matches *target_status* (case-insensitive).
    Returns None if never found.
    """
    target = target_status.lower()
    for hist in changelog_histories:
        for item in hist.items:
            if item.field == "status" and item.toString and item.toString.lower() == target:
                return str(hist.created)
    return None


def fetch_release_epics(
    jira: JIRA,
    search_text: str,
    year: Optional[str] = None,
    release: Optional[str] = None,
) -> List[Epic]:
    """
    Fetch release epics matching *search_text* in the HE project.
    Optionally filter by year (e.g. "2026") or exact release (e.g. "2026.3.0").
    """
    jql = (
        f'project = HE AND type = Epic AND summary ~ "{search_text}" '
        f"ORDER BY created DESC"
    )
    print(f"JQL (epics): {jql}")
    raw = cast(List[Issue], jira.search_issues(jql, maxResults=100, fields="summary,status,created,updated"))

    epics: List[Epic] = []
    for e in raw:
        status = e.fields.status
        epics.append(Epic(
            key=e.key,
            summary=str(e.fields.summary),
            status=status.name if hasattr(status, "name") else str(status),
            created=str(e.fields.created),
            updated=str(e.fields.updated),
        ))

    if release:
        tag = f"[{release}]"
        epics = [e for e in epics if tag in e.summary]
    elif year:
        epics = [e for e in epics if f"[{year}" in e.summary]

    print(f"Found {len(epics)} release epic(s) after filtering")
    return epics


def fetch_children(jira: JIRA, epic_key: str) -> List[ChildIssue]:
    """
    Fetch all child work items of *epic_key* with their changelog.
    start_date = first transition to "Development" (fallback: created).
    done_date  = first transition to "Done" (fallback: resolutiondate).
    """
    jql = f'"Parent" = {epic_key} ORDER BY created ASC'
    fields = (
        "summary,status,priority,assignee,story_points,"
        "customfield_10016,created,updated,resolutiondate,issuetype,duedate"
    )
    raw = cast(List[Issue], jira.search_issues(jql, maxResults=200, fields=fields, expand="changelog"))

    children: List[ChildIssue] = []
    for c in raw:
        f = c.fields

        sp = getattr(f, "story_points", None) or getattr(f, "customfield_10016", None)

        assignee_name = None
        if f.assignee:
            assignee_name = getattr(f.assignee, "displayName", None) or str(f.assignee)

        priority_name = None
        if f.priority:
            priority_name = f.priority.name if hasattr(f.priority, "name") else str(f.priority)

        status_name = f.status.name if hasattr(f.status, "name") else str(f.status)

        issue_type = None
        if f.issuetype:
            issue_type = f.issuetype.name if hasattr(f.issuetype, "name") else str(f.issuetype)

        dev_date = _find_status_date(c.changelog.histories, "Development")
        start_date = dev_date or str(f.created)

        done_date = _find_status_date(c.changelog.histories, "Done")
        end_date = done_date or (str(f.resolutiondate) if f.resolutiondate else None)

        children.append(ChildIssue(
            key=c.key,
            summary=str(f.summary),
            type=issue_type,
            status=status_name,
            priority=priority_name,
            assignee=assignee_name,
            story_points=sp,
            start_date=start_date,
            done_date=end_date,
            due_date=str(f.duedate) if getattr(f, "duedate", None) else None,
            created=str(f.created),
            updated=str(f.updated),
            resolution_date=str(f.resolutiondate) if f.resolutiondate else None,
        ))
    return children
