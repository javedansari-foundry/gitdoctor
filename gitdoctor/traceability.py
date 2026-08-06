"""
MR commit traceability for flow validation (standalone — not used by delta_finder).
"""
from __future__ import annotations

import re
from typing import List, Optional, Set

from .api_client import GitLabAPIError, GitLabClient, GitLabForbidden
from .flow_models import SourceCommitInfo, TraceabilityResult
from .project_resolver import ProjectInfo


JIRA_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")


def extract_jira_tickets(text: str) -> List[str]:
    if not text:
        return []
    return sorted(set(JIRA_PATTERN.findall(text.upper())))


def parse_merge_request_reference(
    message: str,
    default_project_path: str,
) -> Optional[tuple]:
    """
    Parse 'See merge request group/project!123' from squash commit message.
    """
    if not message:
        return None
    pattern = re.compile(
        r"See merge request\s+(?P<path>[^\s!]+)!(?P<iid>\d+)",
        re.IGNORECASE,
    )
    match = pattern.search(message)
    if not match:
        return None
    return match.group("path"), int(match.group("iid"))


class CommitTraceabilityBuilder:
    """Resolve promoted commits back to MR source commits."""

    def __init__(self, client: GitLabClient):
        self.client = client

    def build_for_commit(
        self,
        project: ProjectInfo,
        commit_sha: str,
        commit_message: str = "",
        commit_title: str = "",
    ) -> TraceabilityResult:
        mr_project_id = project.id
        mr_iid: Optional[int] = None
        mr_web_url: Optional[str] = None

        try:
            linked_mrs = self.client.get_commit_merge_requests(project.id, commit_sha)
        except GitLabForbidden as e:
            return TraceabilityResult(status="access_denied", error=str(e))
        except GitLabAPIError:
            linked_mrs = []

        if linked_mrs:
            linked_mrs = sorted(linked_mrs, key=lambda mr: mr.get("iid", 0), reverse=True)
            mr_data = linked_mrs[0]
            mr_iid = mr_data.get("iid")
            mr_web_url = mr_data.get("web_url")
            mr_project_id = mr_data.get("project_id", project.id)
        else:
            parsed = parse_merge_request_reference(
                commit_message or commit_title,
                project.path_with_namespace,
            )
            if not parsed:
                return TraceabilityResult(status="no_mr_link")
            mr_path, mr_iid = parsed
            if mr_path != project.path_with_namespace:
                try:
                    proj = self.client.get_project_by_path(mr_path)
                    mr_project_id = proj.get("id", mr_project_id)
                except GitLabAPIError as e:
                    return TraceabilityResult(
                        status="partial",
                        mr_iid=mr_iid,
                        error=f"Project lookup failed: {e}",
                    )
            mr_web_url = f"{self.client.base_url}/{mr_path}/-/merge_requests/{mr_iid}"

        if not mr_iid:
            return TraceabilityResult(status="partial", error="MR IID missing")

        try:
            mr_commits = self.client.get_merge_request_commits(mr_project_id, mr_iid)
        except GitLabForbidden as e:
            return TraceabilityResult(
                status="access_denied",
                mr_iid=mr_iid,
                mr_web_url=mr_web_url,
                error=str(e),
            )
        except GitLabAPIError as e:
            return TraceabilityResult(
                status="partial",
                mr_iid=mr_iid,
                mr_web_url=mr_web_url,
                error=str(e),
            )

        source_commits: List[SourceCommitInfo] = []
        all_tickets: Set[str] = set()
        for commit in mr_commits:
            sha = commit.get("id", "")
            if not sha:
                continue
            tickets = extract_jira_tickets(
                f"{commit.get('title', '')} {commit.get('message', '')}"
            )
            all_tickets.update(tickets)
            source_commits.append(
                SourceCommitInfo(
                    source_commit_sha=sha,
                    short_id=commit.get("short_id", sha[:8]),
                    title=commit.get("title", ""),
                    jira_tickets=tickets,
                )
            )

        status = "expanded" if source_commits else "partial"
        return TraceabilityResult(
            status=status,
            mr_iid=mr_iid,
            mr_web_url=mr_web_url,
            source_commits=source_commits,
            source_jira_tickets=sorted(all_tickets),
            error=None if source_commits else "MR found but no commits",
        )
