"""
Tests for project resolver functionality.
"""

import pytest
from unittest.mock import Mock

from gitdoctor.project_resolver import (
    ProjectResolver,
    resolve_projects,
    ProjectInfo,
)
from gitdoctor.config import (
    AppConfig,
    GitLabConfig,
    ScanConfig,
    ProjectsConfig,
    GroupsConfig,
    FiltersConfig,
)
from gitdoctor.api_client import GitLabNotFound


@pytest.fixture
def mock_client():
    """Create a mock GitLab client."""
    return Mock()


@pytest.fixture
def sample_gitlab_config():
    """Create sample GitLab configuration."""
    return GitLabConfig(
        base_url="https://gitlab.example.com",
        private_token="test-token"
    )


def test_resolve_projects_explicit_mode_by_id(mock_client, sample_gitlab_config):
    """Test resolving projects in explicit mode by ID."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="explicit"),
        projects=ProjectsConfig(by_id=[1, 2]),
        groups=GroupsConfig(),
        filters=FiltersConfig(),
    )
    
    # Mock API responses
    mock_client.get_project_by_id.side_effect = [
        {
            "id": 1,
            "name": "project1",
            "path_with_namespace": "group/project1",
            "web_url": "url1"
        },
        {
            "id": 2,
            "name": "project2",
            "path_with_namespace": "group/project2",
            "web_url": "url2"
        },
    ]
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    assert len(projects) == 2
    assert projects[0].id == 1
    assert projects[1].id == 2


def test_resolve_projects_explicit_mode_by_path(mock_client, sample_gitlab_config):
    """Test resolving projects in explicit mode by path."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="explicit"),
        projects=ProjectsConfig(by_path=["group/project1", "group/project2"]),
        groups=GroupsConfig(),
        filters=FiltersConfig(),
    )
    
    # Mock API responses
    mock_client.get_project_by_path.side_effect = [
        {
            "id": 10,
            "name": "project1",
            "path_with_namespace": "group/project1",
            "web_url": "url1"
        },
        {
            "id": 20,
            "name": "project2",
            "path_with_namespace": "group/project2",
            "web_url": "url2"
        },
    ]
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    assert len(projects) == 2
    assert projects[0].path_with_namespace == "group/project1"
    assert projects[1].path_with_namespace == "group/project2"


def test_resolve_projects_auto_discover_mode(mock_client, sample_gitlab_config):
    """Test resolving projects in auto_discover mode from groups."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="auto_discover"),
        projects=ProjectsConfig(),
        groups=GroupsConfig(by_path=["test-group"]),
        filters=FiltersConfig(),
    )
    
    # Mock list_group_projects
    mock_client.list_group_projects.return_value = [
        {
            "id": 1,
            "name": "project1",
            "path_with_namespace": "test-group/project1",
            "web_url": "url1"
        },
        {
            "id": 2,
            "name": "project2",
            "path_with_namespace": "test-group/project2",
            "web_url": "url2"
        },
    ]
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    assert len(projects) == 2
    mock_client.list_group_projects.assert_called_once_with(
        "test-group",
        include_subgroups=True
    )


def test_resolve_projects_deduplication(mock_client, sample_gitlab_config):
    """Test that duplicate projects are deduplicated by ID."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="auto_discover"),
        projects=ProjectsConfig(by_id=[1]),  # Explicitly include project 1
        groups=GroupsConfig(by_path=["test-group"]),  # Group also contains project 1
        filters=FiltersConfig(),
    )
    
    # Mock responses - both return project with ID 1
    mock_client.get_project_by_id.return_value = {
        "id": 1,
        "name": "project1",
        "path_with_namespace": "test-group/project1",
        "web_url": "url1"
    }
    
    mock_client.list_group_projects.return_value = [
        {
            "id": 1,
            "name": "project1",
            "path_with_namespace": "test-group/project1",
            "web_url": "url1"
        },
    ]
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    # Should only have 1 project despite being specified twice
    assert len(projects) == 1
    assert projects[0].id == 1


def test_resolve_projects_with_include_filter(mock_client, sample_gitlab_config):
    """Test that include filter works correctly."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="auto_discover"),
        projects=ProjectsConfig(),
        groups=GroupsConfig(by_path=["test-group"]),
        filters=FiltersConfig(
            include_project_paths=["test-group/project1"]
        ),
    )
    
    # Mock list_group_projects returns 3 projects
    mock_client.list_group_projects.return_value = [
        {
            "id": 1,
            "name": "project1",
            "path_with_namespace": "test-group/project1",
            "web_url": "url1"
        },
        {
            "id": 2,
            "name": "project2",
            "path_with_namespace": "test-group/project2",
            "web_url": "url2"
        },
        {
            "id": 3,
            "name": "project3",
            "path_with_namespace": "test-group/project3",
            "web_url": "url3"
        },
    ]
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    # Should only include project1 due to include filter
    assert len(projects) == 1
    assert projects[0].path_with_namespace == "test-group/project1"


def test_resolve_projects_with_exclude_filter(mock_client, sample_gitlab_config):
    """Test that exclude filter works correctly."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="auto_discover"),
        projects=ProjectsConfig(),
        groups=GroupsConfig(by_path=["test-group"]),
        filters=FiltersConfig(
            exclude_project_paths=["test-group/project2"]
        ),
    )
    
    # Mock list_group_projects returns 3 projects
    mock_client.list_group_projects.return_value = [
        {
            "id": 1,
            "name": "project1",
            "path_with_namespace": "test-group/project1",
            "web_url": "url1"
        },
        {
            "id": 2,
            "name": "project2",
            "path_with_namespace": "test-group/project2",
            "web_url": "url2"
        },
        {
            "id": 3,
            "name": "project3",
            "path_with_namespace": "test-group/project3",
            "web_url": "url3"
        },
    ]
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    # Should exclude project2
    assert len(projects) == 2
    paths = [p.path_with_namespace for p in projects]
    assert "test-group/project1" in paths
    assert "test-group/project3" in paths
    assert "test-group/project2" not in paths


def test_resolve_projects_handles_not_found(mock_client, sample_gitlab_config):
    """Test that not found projects are skipped gracefully."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="explicit"),
        projects=ProjectsConfig(by_id=[1, 999, 3]),
        groups=GroupsConfig(),
        filters=FiltersConfig(),
    )
    
    # Mock API - project 999 doesn't exist
    def mock_get_project(project_id):
        if project_id == 999:
            raise GitLabNotFound("Not found", status_code=404)
        return {
            "id": project_id,
            "name": f"project{project_id}",
            "path_with_namespace": f"group/project{project_id}",
            "web_url": f"url{project_id}"
        }
    
    mock_client.get_project_by_id.side_effect = mock_get_project
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    # Should have 2 projects (1 and 3), skipping 999
    assert len(projects) == 2
    project_ids = {p.id for p in projects}
    assert project_ids == {1, 3}


def test_resolve_projects_multiple_groups(mock_client, sample_gitlab_config):
    """Test resolving projects from multiple groups."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="auto_discover"),
        projects=ProjectsConfig(),
        groups=GroupsConfig(by_path=["group1", "group2"]),
        filters=FiltersConfig(),
    )
    
    # Mock list_group_projects to return different projects for each group
    def mock_list_group_projects(group_path, include_subgroups):
        if group_path == "group1":
            return [
                {
                    "id": 1,
                    "name": "project1",
                    "path_with_namespace": "group1/project1",
                    "web_url": "url1"
                },
            ]
        elif group_path == "group2":
            return [
                {
                    "id": 2,
                    "name": "project2",
                    "path_with_namespace": "group2/project2",
                    "web_url": "url2"
                },
            ]
        return []
    
    mock_client.list_group_projects.side_effect = mock_list_group_projects
    
    resolver = ProjectResolver(config, mock_client)
    projects = resolver.resolve_projects()
    
    assert len(projects) == 2
    assert mock_client.list_group_projects.call_count == 2


def test_resolve_projects_include_subgroups_false(mock_client, sample_gitlab_config):
    """Test that include_subgroups setting is passed correctly."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="auto_discover"),
        projects=ProjectsConfig(),
        groups=GroupsConfig(
            by_path=["test-group"],
            include_subgroups=False
        ),
        filters=FiltersConfig(),
    )
    
    mock_client.list_group_projects.return_value = []
    
    resolver = ProjectResolver(config, mock_client)
    resolver.resolve_projects()
    
    # Verify include_subgroups=False is passed
    mock_client.list_group_projects.assert_called_once_with(
        "test-group",
        include_subgroups=False
    )


def test_project_info_equality():
    """Test ProjectInfo equality and hashing."""
    proj1 = ProjectInfo(id=1, name="test", path_with_namespace="group/test", web_url="url")
    proj2 = ProjectInfo(id=1, name="test2", path_with_namespace="group/test2", web_url="url2")
    proj3 = ProjectInfo(id=2, name="test", path_with_namespace="group/test", web_url="url")
    
    # Same ID means equal
    assert proj1 == proj2
    assert hash(proj1) == hash(proj2)
    
    # Different ID means not equal
    assert proj1 != proj3
    assert hash(proj1) != hash(proj3)


def test_convenience_function(mock_client, sample_gitlab_config):
    """Test the convenience resolve_projects function."""
    config = AppConfig(
        gitlab=sample_gitlab_config,
        scan=ScanConfig(mode="explicit"),
        projects=ProjectsConfig(by_id=[1]),
        groups=GroupsConfig(),
        filters=FiltersConfig(),
    )
    
    mock_client.get_project_by_id.return_value = {
        "id": 1,
        "name": "project1",
        "path_with_namespace": "group/project1",
        "web_url": "url1"
    }
    
    # Use the convenience function
    projects = resolve_projects(config, mock_client)
    
    assert len(projects) == 1
    assert projects[0].id == 1

