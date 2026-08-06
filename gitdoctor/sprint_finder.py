"""
Sprint commit finder — aggregates commits across GitLab projects for velocity reporting.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import List, Optional

from .api_client import GitLabClient, GitLabAPIError, GitLabNotFound
from .flow_scope import ref_exists
from .models import SprintCommit, SprintProjectResult, SprintSummary
from .project_resolver import ProjectInfo


logger = logging.getLogger(__name__)

CORE_COMPONENT_PATHS = {
    "dfs-core/product-domains/transaction/shulka",
    "dfs-core/mobiquity-one-issuing/microservices/soe",
    "dfs-core/orchestration/soe-core",
    "dfs-core/sdui/projects/mobiquity/mobiquity-sdui-screens",
    "dfs-core/devops/multinode_mobiquity_deployment",
    "dfs-core/platform/config",
    "dfs-core/devops/ansible_configs",
}


def filter_projects_by_scope(projects: List[ProjectInfo], scope: str) -> List[ProjectInfo]:
    """Filter projects by sprint scope (all, microservices, core)."""
    if scope == "microservices":
        return [p for p in projects if "/microservices/" in p.path_with_namespace]
    if scope == "core":
        return [p for p in projects if p.path_with_namespace in CORE_COMPONENT_PATHS]
    return projects


class SprintFinder:
    """Fetches commits in a date window across multiple GitLab projects."""

    def __init__(self, client: GitLabClient, projects: List[ProjectInfo]):
        self.client = client
        self.projects = projects

    def find_sprint_commits(
        self,
        ref_name: str,
        since: str,
        until: str,
    ) -> List[SprintProjectResult]:
        results: List[SprintProjectResult] = []
        total = len(self.projects)

        logger.info(
            f"Fetching commits on '{ref_name}' across {total} projects "
            f"({since[:10]} → {until[:10]})"
        )

        for idx, project in enumerate(self.projects, 1):
            logger.info(f"[{idx}/{total}] {project.path_with_namespace}")
            results.append(self._fetch_project_commits(project, ref_name, since, until))

        total_commits = sum(len(r.commits) for r in results)
        logger.info(f"Sprint fetch complete. Found {total_commits} commits.")
        return results

    def _fetch_project_commits(
        self,
        project: ProjectInfo,
        ref_name: str,
        since: str,
        until: str,
    ) -> SprintProjectResult:
        result = SprintProjectResult(
            project_id=project.id,
            project_name=project.name,
            project_path=project.path_with_namespace,
            project_web_url=project.web_url,
            ref_name=ref_name,
        )

        try:
            if not ref_exists(self.client, project.id, ref_name):
                result.error = f"Ref '{ref_name}' not found in this project"
                return result

            raw_commits = self.client.list_commits_from_ref(
                project.id, ref_name, since=since, until=until
            )
            for commit in raw_commits:
                result.commits.append(
                    SprintCommit(
                        commit_sha=commit.get("id", ""),
                        short_id=commit.get("short_id", ""),
                        title=commit.get("title", ""),
                        author_name=commit.get("author_name", "Unknown"),
                        author_email=commit.get("author_email", ""),
                        authored_date=commit.get("authored_date", ""),
                        committed_date=commit.get("committed_date", ""),
                        web_url=commit.get("web_url", ""),
                    )
                )
        except GitLabNotFound:
            result.error = f"Ref '{ref_name}' not found in this project"
        except GitLabAPIError as e:
            result.error = str(e)
            logger.warning(f"  ✗ {project.path_with_namespace}: {e}")

        if result.has_commits:
            logger.info(f"  ✓ {len(result.commits)} commits")
        elif result.error:
            logger.warning(f"  ✗ {result.error}")

        return result

    def generate_summary(
        self,
        results: List[SprintProjectResult],
        ref_name: str,
        date_range_start: str,
        date_range_end: str,
        scope: str,
    ) -> SprintSummary:
        commits_by_developer: dict[str, int] = defaultdict(int)
        commits_by_project: dict[str, int] = defaultdict(int)
        velocity_matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for result in results:
            if not result.commits:
                continue
            commits_by_project[result.project_path] = len(result.commits)
            for commit in result.commits:
                commits_by_developer[commit.author_name] += 1
                velocity_matrix[commit.author_name][result.project_path] += 1

        return SprintSummary(
            ref_name=ref_name,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            scope=scope,
            total_projects=len(results),
            projects_with_commits=sum(1 for r in results if r.has_commits),
            projects_with_errors=sum(1 for r in results if r.error),
            total_commits=sum(len(r.commits) for r in results),
            unique_developers=sorted(commits_by_developer.keys()),
            commits_by_developer=dict(commits_by_developer),
            commits_by_project=dict(commits_by_project),
            velocity_matrix={
                dev: dict(projects) for dev, projects in velocity_matrix.items()
            },
        )
