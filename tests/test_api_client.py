"""
Tests for GitLab API client.
"""

import pytest
import responses
from requests.exceptions import Timeout, SSLError

from gitdoctor.api_client import (
    GitLabClient,
    GitLabAPIError,
    GitLabNotFound,
    GitLabUnauthorized,
    GitLabForbidden,
)


@pytest.fixture
def client():
    """Create a test GitLab client."""
    return GitLabClient(
        base_url="https://gitlab.example.com",
        private_token="test-token-123",
        timeout_seconds=5,
    )


@responses.activate
def test_get_project_by_id_success(client):
    """Test successful project fetch by ID."""
    project_data = {
        "id": 123,
        "name": "test-project",
        "path_with_namespace": "group/test-project",
        "web_url": "https://gitlab.example.com/group/test-project"
    }
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123",
        json=project_data,
        status=200
    )
    
    result = client.get_project_by_id(123)
    assert result["id"] == 123
    assert result["name"] == "test-project"


@responses.activate
def test_get_project_by_path_success(client):
    """Test successful project fetch by path."""
    project_data = {
        "id": 456,
        "name": "another-project",
        "path_with_namespace": "group/subgroup/another-project",
        "web_url": "https://gitlab.example.com/group/subgroup/another-project"
    }
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/group%2Fsubgroup%2Fanother-project",
        json=project_data,
        status=200
    )
    
    result = client.get_project_by_path("group/subgroup/another-project")
    assert result["id"] == 456
    assert result["path_with_namespace"] == "group/subgroup/another-project"


@responses.activate
def test_get_project_not_found(client):
    """Test that 404 raises GitLabNotFound."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/999",
        json={"message": "404 Project Not Found"},
        status=404
    )
    
    with pytest.raises(GitLabNotFound):
        client.get_project_by_id(999)


@responses.activate
def test_unauthorized_error(client):
    """Test that 401 raises GitLabUnauthorized."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123",
        json={"message": "401 Unauthorized"},
        status=401
    )
    
    with pytest.raises(GitLabUnauthorized, match="Authentication failed"):
        client.get_project_by_id(123)


@responses.activate
def test_forbidden_error(client):
    """Test that 403 raises GitLabForbidden."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123",
        json={"message": "403 Forbidden"},
        status=403
    )
    
    with pytest.raises(GitLabForbidden, match="Access forbidden"):
        client.get_project_by_id(123)


@responses.activate
def test_server_error(client):
    """Test that 500 raises GitLabAPIError."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123",
        json={"message": "Internal Server Error"},
        status=500
    )
    
    with pytest.raises(GitLabAPIError):
        client.get_project_by_id(123)


@responses.activate
def test_list_group_projects_success(client):
    """Test listing group projects."""
    projects_data = [
        {"id": 1, "name": "project1", "path_with_namespace": "group/project1", "web_url": "url1"},
        {"id": 2, "name": "project2", "path_with_namespace": "group/project2", "web_url": "url2"},
    ]
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/groups/test-group/projects",
        json=projects_data,
        status=200,
        headers={"x-next-page": ""}  # No next page
    )
    
    result = client.list_group_projects("test-group")
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


@responses.activate
def test_list_group_projects_pagination(client):
    """Test that pagination works correctly."""
    page1_data = [
        {"id": 1, "name": "project1", "path_with_namespace": "group/project1", "web_url": "url1"},
    ]
    page2_data = [
        {"id": 2, "name": "project2", "path_with_namespace": "group/project2", "web_url": "url2"},
    ]
    
    # First page
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/groups/test-group/projects",
        json=page1_data,
        status=200,
        headers={"x-next-page": "2"}
    )
    
    # Second page
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/groups/test-group/projects",
        json=page2_data,
        status=200,
        headers={"x-next-page": ""}
    )
    
    result = client.list_group_projects("test-group")
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


@responses.activate
def test_get_commit_success(client):
    """Test successful commit fetch."""
    commit_data = {
        "id": "abc123def456",
        "short_id": "abc123d",
        "title": "Add new feature",
        "author_name": "John Doe",
        "author_email": "john@example.com",
        "created_at": "2024-01-15T10:30:00.000Z",
        "web_url": "https://gitlab.example.com/group/project/commit/abc123def456"
    }
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits/abc123def456",
        json=commit_data,
        status=200
    )
    
    result = client.get_commit(123, "abc123def456")
    assert result["id"] == "abc123def456"
    assert result["title"] == "Add new feature"
    assert result["author_name"] == "John Doe"


@responses.activate
def test_get_commit_not_found(client):
    """Test that commit not found raises GitLabNotFound."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits/notfound",
        json={"message": "404 Commit Not Found"},
        status=404
    )
    
    with pytest.raises(GitLabNotFound):
        client.get_commit(123, "notfound")


@responses.activate
def test_list_commit_refs_success(client):
    """Test listing branches and tags for a commit."""
    refs_data = [
        {"type": "branch", "name": "main"},
        {"type": "branch", "name": "develop"},
        {"type": "tag", "name": "v1.0.0"},
    ]
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits/abc123/refs",
        json=refs_data,
        status=200,
        headers={"x-next-page": ""}
    )
    
    result = client.list_commit_refs(123, "abc123")
    assert len(result) == 3
    assert result[0]["type"] == "branch"
    assert result[0]["name"] == "main"
    assert result[2]["type"] == "tag"


@responses.activate
def test_list_commit_refs_with_type_filter(client):
    """Test listing commit refs with type filter."""
    refs_data = [
        {"type": "branch", "name": "main"},
        {"type": "branch", "name": "develop"},
    ]
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits/abc123/refs",
        json=refs_data,
        status=200,
        headers={"x-next-page": ""}
    )
    
    result = client.list_commit_refs(123, "abc123", ref_type="branch")
    assert len(result) == 2
    assert all(ref["type"] == "branch" for ref in result)


@responses.activate
def test_test_connection_success(client):
    """Test connection test."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/version",
        json={"version": "15.0.0", "revision": "abc123"},
        status=200
    )
    
    result = client.test_connection()
    assert result is True


def test_client_initialization():
    """Test client initialization with various parameters."""
    client = GitLabClient(
        base_url="https://gitlab.example.com/",  # With trailing slash
        private_token="token",
        api_version="v4",
        verify_ssl=False,
        timeout_seconds=30,
    )
    
    assert client.base_url == "https://gitlab.example.com"
    assert client.api_base == "https://gitlab.example.com/api/v4"
    assert client.timeout == 30
    assert client.verify_ssl is False


def test_client_session_headers(client):
    """Test that client sets correct headers."""
    assert "PRIVATE-TOKEN" in client.session.headers
    assert client.session.headers["PRIVATE-TOKEN"] == "test-token-123"
    assert client.session.headers["Content-Type"] == "application/json"


@responses.activate
def test_list_commits_from_ref_success(client):
    """Test listing commits from a ref with pagination."""
    commits_page1 = [
        {
            "id": "abc123",
            "short_id": "abc123",
            "title": "Commit 1",
            "message": "Commit 1",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-09-02T10:00:00Z",
            "committed_date": "2025-09-02T10:00:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": ["parent1"],
            "web_url": "https://gitlab.example.com/commit/abc123"
        }
    ]
    commits_page2 = [
        {
            "id": "def456",
            "short_id": "def456",
            "title": "Commit 2",
            "message": "Commit 2",
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "authored_date": "2025-09-01T10:00:00Z",
            "committed_date": "2025-09-01T10:00:00Z",
            "committer_name": "Jane Smith",
            "committer_email": "jane@example.com",
            "parent_ids": ["parent2"],
            "web_url": "https://gitlab.example.com/commit/def456"
        }
    ]
    
    # First page
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits",
        json=commits_page1,
        status=200,
        headers={"x-next-page": "2"}
    )
    
    # Second page
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits",
        json=commits_page2,
        status=200,
        headers={"x-next-page": ""}
    )
    
    result = client.list_commits_from_ref(123, "v2.0.0")
    
    assert len(result) == 2
    assert result[0]["id"] == "abc123"
    assert result[1]["id"] == "def456"


@responses.activate
def test_list_commits_from_ref_with_date_filters(client):
    """Test listing commits with since/until date filters."""
    commits_data = [
        {
            "id": "abc123",
            "short_id": "abc123",
            "title": "Commit in date range",
            "message": "Commit in date range",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "authored_date": "2025-09-15T10:00:00Z",
            "committed_date": "2025-09-15T10:00:00Z",
            "committer_name": "John Doe",
            "committer_email": "john@example.com",
            "parent_ids": [],
            "web_url": "https://gitlab.example.com/commit/abc123"
        }
    ]
    
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits",
        json=commits_data,
        status=200,
        headers={"x-next-page": ""}
    )
    
    result = client.list_commits_from_ref(
        123,
        "main",
        since="2025-09-01T00:00:00Z",
        until="2025-10-01T00:00:00Z"
    )
    
    assert len(result) == 1
    assert result[0]["id"] == "abc123"


@responses.activate
def test_list_commits_from_ref_empty(client):
    """Test listing commits when no commits exist."""
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/123/repository/commits",
        json=[],
        status=200,
        headers={"x-next-page": ""}
    )
    
    result = client.list_commits_from_ref(123, "empty-branch")
    
    assert len(result) == 0

