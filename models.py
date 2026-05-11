from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Epic:
    key: str
    summary: str
    status: str
    created: str
    updated: str


@dataclass
class ChildIssue:
    key: str
    summary: str
    status: str
    created: str
    updated: str
    type: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    story_points: Optional[float] = None
    start_date: Optional[str] = None
    done_date: Optional[str] = None
    due_date: Optional[str] = None
    resolution_date: Optional[str] = None
