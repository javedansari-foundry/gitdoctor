"""
Tests for commit finder functionality.
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from gitdoctor.commit_finder import (
    CommitFinder,
    CommitSearchResult,
    load_commit_shas_from_file,
)
from gitdoctor.api_client import GitLabNotFound, GitLabAPIError
from gitdoctor.project_resolver import ProjectInfo


@pytest.fixture
def mock_client():
    """Create a mock GitLab client."""
    return Mock()


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
        ),
    ]


def test_commit_found_in_one_project(mock_client, sample_projects):
    """Test finding a commit in one project."""
    commit_sha = "abc123"
    
    # Mock get_commit to succeed for project 1, fail for project 2
    def mock_get_commit(project_id, sha):
        if project_id == 1:
            return {
                "id": sha,
                "title": "Test commit",
                "author_name": "John Doe",
                "author_email": "john@example.com",
                "created_at": "2024-01-15T10:30:00Z",
                "web_url": f"https://gitlab.example.com/group/project1/commit/{sha}"
            }
        raise GitLabNotFound("Not found", status_code=404)
    
    # Mock list_commit_refs
    def mock_list_refs(project_id, sha):
        if project_id == 1:
            return [
                {"type": "branch", "name": "main"},
                {"type": "branch", "name": "develop"},
                {"type": "tag", "name": "v1.0.0"},
            ]
        return []
    
    mock_client.get_commit.side_effect = mock_get_commit
    mock_client.list_commit_refs.side_effect = mock_list_refs
    
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits([commit_sha])
    
    # Should have one result (found in project 1)
    assert len(results) == 1
    result = results[0]
    
    assert result.commit_sha == commit_sha
    assert result.project_id == 1
    assert result.project_name == "project1"
    assert result.found is True
    assert result.title == "Test commit"
    assert result.author_name == "John Doe"
    assert result.branches == "main|develop"
    assert result.tags == "v1.0.0"
    assert result.error == ""


def test_commit_found_in_multiple_projects(mock_client, sample_projects):
    """Test finding a commit in multiple projects."""
    commit_sha = "def456"
    
    # Mock get_commit to succeed for both projects
    def mock_get_commit(project_id, sha):
        return {
            "id": sha,
            "title": f"Commit in project {project_id}",
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "created_at": "2024-01-20T14:00:00Z",
            "web_url": f"https://gitlab.example.com/group/project{project_id}/commit/{sha}"
        }
    
    def mock_list_refs(project_id, sha):
        return [{"type": "branch", "name": f"branch-{project_id}"}]
    
    mock_client.get_commit.side_effect = mock_get_commit
    mock_client.list_commit_refs.side_effect = mock_list_refs
    
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits([commit_sha])
    
    # Should have two results (found in both projects)
    assert len(results) == 2
    
    project_ids = {r.project_id for r in results}
    assert project_ids == {1, 2}
    
    for result in results:
        assert result.commit_sha == commit_sha
        assert result.found is True


def test_commit_not_found_in_any_project(mock_client, sample_projects):
    """Test when a commit is not found in any project."""
    commit_sha = "notfound"
    
    # Mock get_commit to always raise NotFound
    mock_client.get_commit.side_effect = GitLabNotFound("Not found", status_code=404)
    
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits([commit_sha])
    
    # Should have no results when commit is not found
    assert len(results) == 0


def test_multiple_commits_search(mock_client, sample_projects):
    """Test searching for multiple commits."""
    commits = ["abc123", "def456", "ghi789"]
    
    # Mock: abc123 in project 1, def456 in project 2, ghi789 not found
    def mock_get_commit(project_id, sha):
        if sha == "abc123" and project_id == 1:
            return {
                "id": sha,
                "title": "Commit 1",
                "author_name": "Author 1",
                "author_email": "author1@example.com",
                "created_at": "2024-01-01T00:00:00Z",
                "web_url": "url1"
            }
        elif sha == "def456" and project_id == 2:
            return {
                "id": sha,
                "title": "Commit 2",
                "author_name": "Author 2",
                "author_email": "author2@example.com",
                "created_at": "2024-01-02T00:00:00Z",
                "web_url": "url2"
            }
        raise GitLabNotFound("Not found", status_code=404)
    
    mock_client.get_commit.side_effect = mock_get_commit
    mock_client.list_commit_refs.return_value = []
    
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits(commits)
    
    # Should find 2 commits (abc123 and def456)
    assert len(results) == 2
    
    found_commits = {r.commit_sha for r in results}
    assert found_commits == {"abc123", "def456"}


def test_api_error_handling(mock_client, sample_projects):
    """Test handling of API errors during search."""
    commit_sha = "error123"
    
    # Mock get_commit to raise an API error for project 1
    def mock_get_commit(project_id, sha):
        if project_id == 1:
            raise GitLabAPIError("Server error", status_code=500)
        raise GitLabNotFound("Not found", status_code=404)
    
    mock_client.get_commit.side_effect = mock_get_commit
    
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits([commit_sha])
    
    # Should have one result with error recorded
    assert len(results) == 1
    result = results[0]
    
    assert result.commit_sha == commit_sha
    assert result.project_id == 1
    assert result.found is False
    assert "Server error" in result.error


def test_refs_fetch_error_handling(mock_client, sample_projects):
    """Test handling when commit is found but refs fetch fails."""
    commit_sha = "abc123"
    
    # Mock get_commit to succeed
    mock_client.get_commit.return_value = {
        "id": commit_sha,
        "title": "Test commit",
        "author_name": "John Doe",
        "author_email": "john@example.com",
        "created_at": "2024-01-15T10:30:00Z",
        "web_url": "url"
    }
    
    # Mock list_commit_refs to fail
    mock_client.list_commit_refs.side_effect = GitLabAPIError("Refs error")
    
    finder = CommitFinder(mock_client, [sample_projects[0]])
    results = finder.search_commits([commit_sha])
    
    # Should still return commit info, but with error noted
    assert len(results) == 1
    result = results[0]
    
    assert result.found is True
    assert result.title == "Test commit"
    assert result.branches == ""
    assert result.tags == ""
    assert "Could not fetch refs" in result.error


def test_load_commit_shas_from_file():
    """Test loading commit SHAs from a file."""
    content = """
    abc123def456
    
    ghi789jkl012
    
    mno345pqr678
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        f.flush()
        
        commits = load_commit_shas_from_file(f.name)
        
        assert len(commits) == 3
        assert commits[0] == "abc123def456"
        assert commits[1] == "ghi789jkl012"
        assert commits[2] == "mno345pqr678"
        
        Path(f.name).unlink()


def test_load_commit_shas_from_file_not_found():
    """Test that loading from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_commit_shas_from_file("nonexistent.txt")


def test_load_commit_shas_empty_file():
    """Test loading from empty file returns empty list."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("\n\n\n")
        f.flush()
        
        commits = load_commit_shas_from_file(f.name)
        assert len(commits) == 0
        
        Path(f.name).unlink()


def test_commit_search_result_initialization():
    """Test CommitSearchResult initialization."""
    result = CommitSearchResult(
        commit_sha="abc123",
        project_id=1,
        project_name="test",
        project_path="group/test",
        project_web_url="url"
    )
    
    assert result.commit_sha == "abc123"
    assert result.project_id == 1
    assert result.found is False
    assert result.error == ""
    assert result.branches == ""
    assert result.tags == ""


def test_empty_commits_list(mock_client, sample_projects):
    """Test searching with empty commits list."""
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits([])
    
    assert len(results) == 0


def test_whitespace_only_commits_ignored(mock_client, sample_projects):
    """Test that whitespace-only lines are ignored."""
    commits = ["abc123", "  ", "\t", "", "def456"]
    
    def mock_get_commit(project_id, sha):
        return {
            "id": sha,
            "title": "Test",
            "author_name": "Author",
            "author_email": "email",
            "created_at": "2024-01-01T00:00:00Z",
            "web_url": "url"
        }
    
    mock_client.get_commit.side_effect = mock_get_commit
    mock_client.list_commit_refs.return_value = []
    
    finder = CommitFinder(mock_client, sample_projects)
    results = finder.search_commits(commits)
    
    # Should process only abc123 and def456 (2 commits x 2 projects = 4 results)
    assert len(results) == 4

