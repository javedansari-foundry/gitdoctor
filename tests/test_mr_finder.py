"""
Tests for MR finder module.
"""
from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
from gitdoctor.mr_finder import MRFinder
from gitdoctor.models import MergeRequest, MRResult, MRSummary


class MockProjectInfo:
    """Mock ProjectInfo for testing."""
    def __init__(self, project_id, name, path, web_url):
        self.id = project_id
        self.name = name
        self.path_with_namespace = path
        self.web_url = web_url


class TestMergeRequestModel:
    """Tests for MergeRequest dataclass."""
    
    def test_from_api_response(self):
        """Test creating MergeRequest from API response."""
        api_data = {
            "id": 12345,
            "iid": 42,
            "title": "Fix bug in login",
            "description": "This fixes the login issue",
            "state": "merged",
            "source_branch": "fix/login-bug",
            "target_branch": "master",
            "author": {
                "name": "John Doe",
                "username": "johndoe"
            },
            "merged_by": {
                "name": "Jane Smith",
                "username": "janesmith"
            },
            "merged_at": "2025-01-15T10:30:00Z",
            "created_at": "2025-01-10T09:00:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
            "web_url": "http://gitlab.example.com/project/-/merge_requests/42",
            "merge_commit_sha": "abc123def456",
            "labels": ["bug", "urgent"]
        }
        
        mr = MergeRequest.from_api_response(api_data)
        
        assert mr.mr_id == 12345
        assert mr.mr_iid == 42
        assert mr.title == "Fix bug in login"
        assert mr.description == "This fixes the login issue"
        assert mr.state == "merged"
        assert mr.source_branch == "fix/login-bug"
        assert mr.target_branch == "master"
        assert mr.author_name == "John Doe"
        assert mr.author_username == "johndoe"
        assert mr.merged_by_name == "Jane Smith"
        assert mr.merged_by_username == "janesmith"
        assert mr.merged_at == "2025-01-15T10:30:00Z"
        assert mr.merge_commit_sha == "abc123def456"
        assert mr.labels == ["bug", "urgent"]
    
    def test_from_api_response_without_merged_by(self):
        """Test MergeRequest when merged_by is None."""
        api_data = {
            "id": 123,
            "iid": 1,
            "title": "Open MR",
            "description": "",
            "state": "opened",
            "source_branch": "feature",
            "target_branch": "master",
            "author": {"name": "Dev", "username": "dev"},
            "merged_by": None,
            "merged_at": None,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "web_url": "http://example.com/mr/1",
            "merge_commit_sha": None,
            "labels": []
        }
        
        mr = MergeRequest.from_api_response(api_data)
        
        assert mr.merged_by_name is None
        assert mr.merged_by_username is None
        assert mr.merged_at is None


class TestMRResult:
    """Tests for MRResult dataclass."""
    
    def test_has_mrs_true(self):
        """Test has_mrs when MRs exist."""
        result = MRResult(
            project_id=1,
            project_name="test",
            project_path="test/project",
            project_web_url="http://example.com"
        )
        result.merge_requests = [Mock()]
        
        assert result.has_mrs is True
    
    def test_has_mrs_false(self):
        """Test has_mrs when no MRs."""
        result = MRResult(
            project_id=1,
            project_name="test",
            project_path="test/project",
            project_web_url="http://example.com"
        )
        
        assert result.has_mrs is False
    
    def test_is_successful_true(self):
        """Test is_successful when no error."""
        result = MRResult(
            project_id=1,
            project_name="test",
            project_path="test/project",
            project_web_url="http://example.com"
        )
        
        assert result.is_successful is True
    
    def test_is_successful_false_with_error(self):
        """Test is_successful when there's an error."""
        result = MRResult(
            project_id=1,
            project_name="test",
            project_path="test/project",
            project_web_url="http://example.com",
            error="API error"
        )
        
        assert result.is_successful is False
    
    def test_get_unique_authors(self):
        """Test getting unique authors."""
        result = MRResult(
            project_id=1,
            project_name="test",
            project_path="test/project",
            project_web_url="http://example.com"
        )
        
        mr1 = Mock()
        mr1.author_name = "Alice"
        mr2 = Mock()
        mr2.author_name = "Bob"
        mr3 = Mock()
        mr3.author_name = "Alice"  # Duplicate
        
        result.merge_requests = [mr1, mr2, mr3]
        
        authors = result.get_unique_authors()
        assert authors == ["Alice", "Bob"]


class TestMRSummary:
    """Tests for MRSummary dataclass."""
    
    def test_str_output(self):
        """Test summary string output."""
        summary = MRSummary(
            target_branch="master",
            source_branch=None,
            state_filter="merged",
            date_range_start="2025-01-01",
            date_range_end="2025-01-31",
            total_projects=5,
            projects_with_mrs=3,
            projects_with_errors=0,
            total_mrs=42,
            unique_authors=["Alice", "Bob", "Charlie"],
            top_projects=[("project-a", 20), ("project-b", 15), ("project-c", 7)]
        )
        
        output = str(summary)
        
        assert "Merge Request Summary" in output
        assert "master" in output
        assert "merged" in output
        assert "Total Merge Requests:    42" in output
        assert "Unique Authors:          3" in output
        assert "project-a: 20 MRs" in output


class TestMRFinder:
    """Tests for MRFinder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.projects = [
            MockProjectInfo(1, "project-a", "group/project-a", "http://example.com/a"),
            MockProjectInfo(2, "project-b", "group/project-b", "http://example.com/b"),
        ]
        self.finder = MRFinder(self.mock_client, self.projects)
    
    def test_find_merge_requests_success(self):
        """Test finding MRs across projects."""
        # Mock API responses
        self.mock_client.list_merge_requests.side_effect = [
            # Project 1 MRs
            [
                {
                    "id": 100, "iid": 1, "title": "MR 1",
                    "description": "", "state": "merged",
                    "source_branch": "feature-1", "target_branch": "master",
                    "author": {"name": "Dev 1", "username": "dev1"},
                    "merged_by": {"name": "Lead", "username": "lead"},
                    "merged_at": "2025-01-10T00:00:00Z",
                    "created_at": "2025-01-05T00:00:00Z",
                    "updated_at": "2025-01-10T00:00:00Z",
                    "web_url": "http://example.com/mr/1",
                    "merge_commit_sha": "sha1",
                    "labels": []
                }
            ],
            # Project 2 MRs
            [
                {
                    "id": 200, "iid": 2, "title": "MR 2",
                    "description": "", "state": "merged",
                    "source_branch": "feature-2", "target_branch": "master",
                    "author": {"name": "Dev 2", "username": "dev2"},
                    "merged_by": None,
                    "merged_at": "2025-01-15T00:00:00Z",
                    "created_at": "2025-01-12T00:00:00Z",
                    "updated_at": "2025-01-15T00:00:00Z",
                    "web_url": "http://example.com/mr/2",
                    "merge_commit_sha": "sha2",
                    "labels": []
                }
            ]
        ]
        
        results = self.finder.find_merge_requests(
            target_branch="master",
            state="merged"
        )
        
        assert len(results) == 2
        assert results[0].total_mrs == 1
        assert results[1].total_mrs == 1
        assert results[0].merge_requests[0].title == "MR 1"
        assert results[1].merge_requests[0].title == "MR 2"
    
    def test_find_merge_requests_with_date_filter(self):
        """Test finding MRs with date filter."""
        self.mock_client.list_merge_requests.return_value = []
        
        self.finder.find_merge_requests(
            target_branch="master",
            merged_after="2025-01-01T00:00:00Z",
            merged_before="2025-01-31T23:59:59Z"
        )
        
        # Verify date filters were passed to API
        call_args = self.mock_client.list_merge_requests.call_args_list[0]
        assert call_args.kwargs.get("merged_after") == "2025-01-01T00:00:00Z"
        assert call_args.kwargs.get("merged_before") == "2025-01-31T23:59:59Z"
    
    def test_find_merge_requests_handles_api_error(self):
        """Test graceful handling of API errors."""
        from gitdoctor.api_client import GitLabAPIError
        
        self.mock_client.list_merge_requests.side_effect = [
            GitLabAPIError("API rate limit exceeded"),
            []  # Second project succeeds
        ]
        
        results = self.finder.find_merge_requests(state="merged")
        
        assert len(results) == 2
        assert results[0].error is not None
        assert "API error" in results[0].error
        assert results[1].is_successful is True
    
    def test_generate_summary(self):
        """Test generating summary from results."""
        # Create mock results
        mr1 = MergeRequest(
            mr_id=1, mr_iid=1, title="MR 1", description="",
            state="merged", source_branch="feature", target_branch="master",
            author_name="Alice", author_username="alice"
        )
        mr2 = MergeRequest(
            mr_id=2, mr_iid=2, title="MR 2", description="",
            state="merged", source_branch="bugfix", target_branch="master",
            author_name="Bob", author_username="bob"
        )
        mr3 = MergeRequest(
            mr_id=3, mr_iid=3, title="MR 3", description="",
            state="merged", source_branch="feature2", target_branch="master",
            author_name="Alice", author_username="alice"
        )
        
        result1 = MRResult(
            project_id=1, project_name="project-a",
            project_path="group/project-a", project_web_url="http://example.com/a",
            target_branch="master", state_filter="merged"
        )
        result1.merge_requests = [mr1, mr2]
        result1.total_mrs = 2
        
        result2 = MRResult(
            project_id=2, project_name="project-b",
            project_path="group/project-b", project_web_url="http://example.com/b",
            target_branch="master", state_filter="merged"
        )
        result2.merge_requests = [mr3]
        result2.total_mrs = 1
        
        summary = self.finder.generate_summary([result1, result2])
        
        assert summary.total_projects == 2
        assert summary.projects_with_mrs == 2
        assert summary.total_mrs == 3
        assert len(summary.unique_authors) == 2
        assert "Alice" in summary.unique_authors
        assert "Bob" in summary.unique_authors
        assert summary.top_projects[0] == ("group/project-a", 2)





