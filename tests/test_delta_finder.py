"""
Tests for delta_finder module.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from gitdoctor.delta_finder import DeltaFinder
from gitdoctor.models import DeltaResult, DeltaCommit, DeltaSummary
from gitdoctor.project_resolver import ProjectInfo
from gitdoctor.api_client import GitLabNotFound, GitLabAPIError


@pytest.fixture
def mock_client():
    """Create a mock GitLab client."""
    client = Mock()
    return client


@pytest.fixture
def sample_projects():
    """Create sample projects for testing."""
    return [
        ProjectInfo(
            id=1,
            name="project1",
            path_with_namespace="group/project1",
            web_url="https://gitlab.example.com/group/project1"
        ),
        ProjectInfo(
            id=2,
            name="project2",
            path_with_namespace="group/project2",
            web_url="https://gitlab.example.com/group/project2"
        )
    ]


def test_delta_finder_with_commits(mock_client, sample_projects):
    """Test finding delta with commits between refs using set difference."""
    # Mock tag/branch checks
    mock_client.get_tag.return_value = {"name": "v1.0.0"}
    
    # Mock paginated commits from target ref (includes commits unique to target + shared)
    target_commits = [
        {
            "id": "abc123",
            "short_id": "abc123",
            "title": "Feature A",
            "message": "Add feature A",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-09-01T10:00:00Z",
            "committed_date": "2025-09-01T10:30:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": ["parent1"],
            "web_url": "https://gitlab.example.com/group/project1/commit/abc123"
        },
        {
            "id": "def456",
            "short_id": "def456",
            "title": "Fix bug B",
            "message": "Fix bug B",
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "authored_date": "2025-09-02T11:00:00Z",
            "committed_date": "2025-09-02T11:30:00Z",
            "committer_name": "Jane Smith",
            "committer_email": "jane@example.com",
            "parent_ids": ["parent2"],
            "web_url": "https://gitlab.example.com/group/project1/commit/def456"
        },
        {
            "id": "shared123",
            "short_id": "shared1",
            "title": "Shared commit",
            "message": "Shared commit",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-08-01T10:00:00Z",
            "committed_date": "2025-08-01T10:00:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": [],
            "web_url": "https://gitlab.example.com/group/project1/commit/shared123"
        }
    ]
    
    # Mock paginated commits from base ref (shared commits only)
    base_commits = [
        {
            "id": "shared123",
            "short_id": "shared1",
            "title": "Shared commit",
            "message": "Shared commit",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-08-01T10:00:00Z",
            "committed_date": "2025-08-01T10:00:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": [],
            "web_url": "https://gitlab.example.com/group/project1/commit/shared123"
        }
    ]
    
    def mock_list_commits(project_id, ref_name):
        if ref_name == "v2.0.0":
            return target_commits
        else:
            return base_commits
    
    mock_client.list_commits_from_ref.side_effect = mock_list_commits
    
    finder = DeltaFinder(mock_client, [sample_projects[0]])
    deltas = finder.find_deltas("v1.0.0", "v2.0.0")
    
    assert len(deltas) == 1
    delta = deltas[0]
    
    assert delta.project_id == 1
    assert delta.project_name == "project1"
    assert delta.base_ref == "v1.0.0"
    assert delta.target_ref == "v2.0.0"
    assert delta.base_exists is True
    assert delta.target_exists is True
    assert len(delta.commits) == 2  # Only abc123 and def456 (not shared123)
    assert delta.total_commits == 2
    assert delta.has_changes is True
    assert delta.is_successful is True
    assert delta.error is None
    
    # Check commits are sorted by date (newest first)
    commit_shas = [c.commit_sha for c in delta.commits]
    assert "abc123" in commit_shas
    assert "def456" in commit_shas
    assert "shared123" not in commit_shas  # Shared commit should be excluded


def test_delta_finder_no_commits(mock_client, sample_projects):
    """Test finding delta when refs are identical (no commits between them)."""
    # Mock tag checks
    mock_client.get_tag.return_value = {"name": "v1.0.0"}
    
    # Both refs return the same commits (identical refs)
    same_commits = [
        {
            "id": "abc123",
            "short_id": "abc123",
            "title": "Existing commit",
            "message": "Existing commit",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-09-01T10:00:00Z",
            "committed_date": "2025-09-01T10:00:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": [],
            "web_url": "https://gitlab.example.com/commit/abc123"
        }
    ]
    
    mock_client.list_commits_from_ref.return_value = same_commits
    
    finder = DeltaFinder(mock_client, [sample_projects[0]])
    deltas = finder.find_deltas("v1.0.0", "v1.0.0")
    
    assert len(deltas) == 1
    delta = deltas[0]
    
    assert delta.has_changes is False
    assert len(delta.commits) == 0
    assert delta.compare_same_ref is True


def test_delta_finder_base_ref_not_found(mock_client, sample_projects):
    """Test when base ref doesn't exist in project."""
    # Base ref not found
    mock_client.get_tag.side_effect = GitLabNotFound("Tag not found")
    mock_client.get_branch.side_effect = GitLabNotFound("Branch not found")
    mock_client.get_commit.side_effect = GitLabNotFound("Commit not found")
    
    finder = DeltaFinder(mock_client, [sample_projects[0]])
    deltas = finder.find_deltas("nonexistent-tag", "v2.0.0")
    
    assert len(deltas) == 1
    delta = deltas[0]
    
    assert delta.base_exists is False
    assert delta.error is not None
    assert "Base ref" in delta.error
    assert delta.has_changes is False


def test_delta_finder_target_ref_not_found(mock_client, sample_projects):
    """Test when target ref doesn't exist in project."""
    # Base exists, target doesn't
    mock_client.get_tag.side_effect = [
        {"name": "v1.0.0"},  # Base exists
        GitLabNotFound("Tag not found")  # Target doesn't
    ]
    mock_client.get_branch.side_effect = GitLabNotFound("Branch not found")
    mock_client.get_commit.side_effect = GitLabNotFound("Commit not found")
    
    finder = DeltaFinder(mock_client, [sample_projects[0]])
    deltas = finder.find_deltas("v1.0.0", "nonexistent-tag")
    
    assert len(deltas) == 1
    delta = deltas[0]
    
    assert delta.base_exists is True
    assert delta.target_exists is False
    assert delta.error is not None
    assert "Target ref" in delta.error


def test_delta_finder_with_date_filter(mock_client, sample_projects):
    """Test delta finding with date filtering."""
    mock_client.get_tag.return_value = {"name": "v1.0.0"}
    
    # Target ref has two commits with different dates
    target_commits = [
        {
            "id": "abc123",
            "short_id": "abc123",
            "title": "Old commit",
            "message": "Old commit",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-08-01T10:00:00Z",
            "committed_date": "2025-08-01T10:00:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": [],
            "web_url": "https://gitlab.example.com/commit/abc123"
        },
        {
            "id": "def456",
            "short_id": "def456",
            "title": "New commit",
            "message": "New commit",
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "authored_date": "2025-09-15T10:00:00Z",
            "committed_date": "2025-09-15T10:00:00Z",
            "committer_name": "Jane Smith",
            "committer_email": "jane@example.com",
            "parent_ids": [],
            "web_url": "https://gitlab.example.com/commit/def456"
        }
    ]
    
    # Base ref has no commits (empty)
    base_commits = []
    
    def mock_list_commits(project_id, ref_name):
        if ref_name == "v2.0.0":
            return target_commits
        else:
            return base_commits
    
    mock_client.list_commits_from_ref.side_effect = mock_list_commits
    
    finder = DeltaFinder(mock_client, [sample_projects[0]])
    
    # Filter to only include commits after 2025-09-01
    deltas = finder.find_deltas(
        "v1.0.0",
        "v2.0.0",
        after_date="2025-09-01T00:00:00Z"
    )
    
    assert len(deltas) == 1
    delta = deltas[0]
    
    # Should only include the new commit (after date filter)
    assert len(delta.commits) == 1
    assert delta.commits[0].commit_sha == "def456"
    assert delta.total_commits == 2  # Total before date filtering


def test_delta_finder_multiple_projects(mock_client, sample_projects):
    """Test finding deltas across multiple projects using set difference."""
    # Mock responses for both projects
    mock_client.get_tag.return_value = {"name": "v1.0.0"}
    
    def mock_list_commits(project_id, ref_name):
        if project_id == 1:
            if ref_name == "v2.0.0":
                return [
                    {
                        "id": "abc123",
                        "short_id": "abc123",
                        "title": "Commit in project 1",
                        "message": "Commit in project 1",
                        "author_name": "John Doe",
                        "author_email": "john@example.com",
                        "authored_date": "2025-09-01T10:00:00Z",
                        "committed_date": "2025-09-01T10:00:00Z",
                        "committer_name": "John Doe",
                        "committer_email": "john@example.com",
                        "parent_ids": [],
                        "web_url": "https://gitlab.example.com/commit/abc123"
                    }
                ]
            else:
                return []  # Base has no commits
        else:  # project_id == 2
            if ref_name == "v2.0.0":
                return [
                    {
                        "id": "def456",
                        "short_id": "def456",
                        "title": "Commit in project 2",
                        "message": "Commit in project 2",
                        "author_name": "Jane Smith",
                        "author_email": "jane@example.com",
                        "authored_date": "2025-09-02T10:00:00Z",
                        "committed_date": "2025-09-02T10:00:00Z",
                        "committer_name": "Jane Smith",
                        "committer_email": "jane@example.com",
                        "parent_ids": [],
                        "web_url": "https://gitlab.example.com/commit/def456"
                    }
                ]
            else:
                return []  # Base has no commits
    
    mock_client.list_commits_from_ref.side_effect = mock_list_commits
    
    finder = DeltaFinder(mock_client, sample_projects)
    deltas = finder.find_deltas("v1.0.0", "v2.0.0")
    
    assert len(deltas) == 2
    assert deltas[0].commits[0].commit_sha == "abc123"
    assert deltas[1].commits[0].commit_sha == "def456"


def test_generate_summary(mock_client, sample_projects):
    """Test summary generation from delta results."""
    # Create mock deltas
    deltas = [
        DeltaResult(
            project_id=1,
            project_name="project1",
            project_path="group/project1",
            project_web_url="https://gitlab.example.com/group/project1",
            base_ref="v1.0.0",
            target_ref="v2.0.0",
            base_exists=True,
            target_exists=True,
            commits=[
                DeltaCommit(
                    commit_sha="abc123",
                    short_id="abc123",
                    title="Commit 1",
                    message="Commit 1",
                    author_name="John Doe",
                    author_email="john@example.com",
                    authored_date="2025-09-01T10:00:00Z",
                    committed_date="2025-09-01T10:00:00Z",
                    committer_name="John Doe",
                    committer_email="john@example.com",
                    web_url="https://gitlab.example.com/commit/abc123",
                    parent_ids=[]
                ),
                DeltaCommit(
                    commit_sha="def456",
                    short_id="def456",
                    title="Commit 2",
                    message="Commit 2",
                    author_name="Jane Smith",
                    author_email="jane@example.com",
                    authored_date="2025-09-02T10:00:00Z",
                    committed_date="2025-09-02T10:00:00Z",
                    committer_name="Jane Smith",
                    committer_email="jane@example.com",
                    web_url="https://gitlab.example.com/commit/def456",
                    parent_ids=[]
                )
            ],
            total_commits=2,
            files_changed=5
        ),
        DeltaResult(
            project_id=2,
            project_name="project2",
            project_path="group/project2",
            project_web_url="https://gitlab.example.com/group/project2",
            base_ref="v1.0.0",
            target_ref="v2.0.0",
            base_exists=True,
            target_exists=True,
            commits=[],
            total_commits=0,
            files_changed=0
        )
    ]
    
    finder = DeltaFinder(mock_client, sample_projects)
    summary = finder.generate_summary(deltas)
    
    assert summary.base_ref == "v1.0.0"
    assert summary.target_ref == "v2.0.0"
    assert summary.total_projects == 2
    assert summary.projects_with_changes == 1
    assert summary.projects_without_changes == 1
    assert summary.total_commits == 2
    assert summary.total_files_changed == 5
    assert len(summary.unique_authors) == 2
    assert "John Doe" in summary.unique_authors
    assert "Jane Smith" in summary.unique_authors
    assert len(summary.top_projects) == 1
    assert summary.top_projects[0] == ("group/project1", 2)


def test_delta_result_properties():
    """Test DeltaResult helper properties."""
    delta = DeltaResult(
        project_id=1,
        project_name="project1",
        project_path="group/project1",
        project_web_url="https://gitlab.example.com/group/project1",
        base_ref="v1.0.0",
        target_ref="v2.0.0",
        base_exists=True,
        target_exists=True,
        commits=[
            DeltaCommit(
                commit_sha="abc123",
                short_id="abc123",
                title="Test",
                message="Test",
                author_name="John Doe",
                author_email="john@example.com",
                authored_date="2025-09-01T10:00:00Z",
                committed_date="2025-09-01T10:00:00Z",
                committer_name="John Doe",
                committer_email="john@example.com",
                web_url="https://gitlab.example.com/commit/abc123",
                parent_ids=[]
            )
        ]
    )
    
    assert delta.has_changes is True
    assert delta.is_successful is True
    
    authors = delta.get_unique_authors()
    assert len(authors) == 1
    assert authors[0] == "John Doe"
    
    commits_by_author = delta.get_commits_by_author("John Doe")
    assert len(commits_by_author) == 1

