import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, Field


class RepoConnectRequest(BaseModel):
    owner: str
    name: str
    github_token: Optional[str] = Field(
        default=None,
        description="Optional per-repo token override. Falls back to server GITHUB_TOKEN.",
    )


class RepositoryOut(BaseModel):
    id: int
    owner: str
    name: str
    full_name: str
    default_branch: Optional[str]
    description: Optional[str]
    created_at: dt.datetime

    class Config:
        from_attributes = True


class CommitOut(BaseModel):
    sha: str
    short_sha: str
    message: str
    author: Optional[str]
    date: Optional[dt.datetime]
    files_changed: int


class ScanCreateRequest(BaseModel):
    repository_id: int
    commit_sha: str


class FindingOut(BaseModel):
    id: int
    doc_path: str
    severity: str
    summary: str
    suggested_patch: Optional[str]
    pr_url: Optional[str]

    class Config:
        from_attributes = True


class ScanOut(BaseModel):
    id: int
    repository_id: int
    commit_sha: str
    commit_message: Optional[str]
    status: str
    error_message: Optional[str]
    diff_analysis: Optional[str]
    created_at: dt.datetime
    completed_at: Optional[dt.datetime]
    findings: List[FindingOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CreatePRRequest(BaseModel):
    finding_ids: List[int]
    branch_name: Optional[str] = None
    pr_title: Optional[str] = None
