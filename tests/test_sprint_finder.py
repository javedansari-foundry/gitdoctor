"""Tests for sprint velocity finder."""
from __future__ import annotations

from unittest.mock import Mock

from gitdoctor.sprint_finder import SprintFinder, filter_projects_by_scope
from gitdoctor.models import SprintCommit, SprintProjectResult


class MockProjectInfo:
    def __init__(self, project_id, name, path, web_url="http://example.com"):
        self.id = project_id
        self.name = name
        self.path_with_namespace = path
        self.web_url = web_url


class TestFilterProjectsByScope:
    def test_microservices_scope(self):
        projects = [
            MockProjectInfo(1, "soe", "dfs-core/mobiquity-one-issuing/microservices/soe"),
            MockProjectInfo(2, "shulka", "dfs-core/product-domains/transaction/shulka"),
        ]
        filtered = filter_projects_by_scope(projects, "microservices")
        assert len(filtered) == 1
        assert filtered[0].name == "soe"

    def test_core_scope(self):
        projects = [
            MockProjectInfo(1, "soe", "dfs-core/mobiquity-one-issuing/microservices/soe"),
            MockProjectInfo(2, "shulka", "dfs-core/product-domains/transaction/shulka"),
        ]
        filtered = filter_projects_by_scope(projects, "core")
        assert len(filtered) == 2


class TestSprintFinder:
    def test_generate_summary(self):
        client = Mock()
        finder = SprintFinder(client, [])
        results = [
            SprintProjectResult(
                project_id=1,
                project_name="soe",
                project_path="dfs-core/mobiquity-one-issuing/microservices/soe",
                project_web_url="http://example.com/soe",
                ref_name="premaster",
                commits=[
                    SprintCommit(
                        commit_sha="abc",
                        short_id="abc",
                        title="Fix bug",
                        author_name="Alice",
                        author_email="alice@example.com",
                        authored_date="2026-06-01",
                        committed_date="2026-06-01",
                        web_url="http://example.com/commit/abc",
                    ),
                    SprintCommit(
                        commit_sha="def",
                        short_id="def",
                        title="Add feature",
                        author_name="Bob",
                        author_email="bob@example.com",
                        authored_date="2026-06-02",
                        committed_date="2026-06-02",
                        web_url="http://example.com/commit/def",
                    ),
                ],
            ),
            SprintProjectResult(
                project_id=2,
                project_name="shulka",
                project_path="dfs-core/product-domains/transaction/shulka",
                project_web_url="http://example.com/shulka",
                ref_name="premaster",
                commits=[
                    SprintCommit(
                        commit_sha="ghi",
                        short_id="ghi",
                        title="Update config",
                        author_name="Alice",
                        author_email="alice@example.com",
                        authored_date="2026-06-03",
                        committed_date="2026-06-03",
                        web_url="http://example.com/commit/ghi",
                    ),
                ],
            ),
        ]

        summary = finder.generate_summary(
            results,
            ref_name="premaster",
            date_range_start="2026-05-26",
            date_range_end="2026-06-09",
            scope="all",
        )

        assert summary.total_commits == 3
        assert len(summary.unique_developers) == 2
        assert summary.commits_by_developer["Alice"] == 2
        assert summary.commits_by_developer["Bob"] == 1
        assert summary.velocity_matrix["Alice"]["dfs-core/mobiquity-one-issuing/microservices/soe"] == 1
        assert summary.velocity_matrix["Alice"]["dfs-core/product-domains/transaction/shulka"] == 1
