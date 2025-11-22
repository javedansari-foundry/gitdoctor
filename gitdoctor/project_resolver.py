"""
Project resolver module.

Resolves which GitLab projects to search based on configuration.
Supports auto-discovery from groups or explicit project lists.
"""

from dataclasses import dataclass
from typing import List, Set, Dict
import logging

from .config import AppConfig
from .api_client import GitLabClient, GitLabNotFound, GitLabAPIError


logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Information about a GitLab project."""
    id: int
    name: str
    path_with_namespace: str
    web_url: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, ProjectInfo):
            return False
        return self.id == other.id


class ProjectResolver:
    """
    Resolves which projects to search based on configuration.
    
    Supports two modes:
    - auto_discover: Discover all projects from configured groups
    - explicit: Use only explicitly configured projects
    """

    def __init__(self, config: AppConfig, client: GitLabClient):
        """
        Initialize project resolver.

        Args:
            config: Application configuration
            client: GitLab API client
        """
        self.config = config
        self.client = client

    def resolve_projects(self) -> List[ProjectInfo]:
        """
        Resolve the list of projects to search.

        Returns:
            List of ProjectInfo objects, deduplicated by project ID

        Raises:
            GitLabAPIError: If API calls fail
        """
        projects: Dict[int, ProjectInfo] = {}  # Use dict to deduplicate by ID
        
        if self.config.scan.mode == "auto_discover":
            logger.info("Running in auto_discover mode")
            projects.update(self._discover_from_groups())
            # In auto_discover mode, also include explicitly listed projects if any
            if self.config.projects.by_id or self.config.projects.by_path:
                logger.info("Also including explicitly configured projects")
                projects.update(self._get_explicit_projects())
        else:  # explicit mode
            logger.info("Running in explicit mode")
            projects.update(self._get_explicit_projects())

        # Apply filters
        filtered_projects = self._apply_filters(list(projects.values()))
        
        logger.info(f"Resolved {len(filtered_projects)} projects to search")
        return filtered_projects

    def _discover_from_groups(self) -> Dict[int, ProjectInfo]:
        """
        Discover projects from configured groups.

        Returns:
            Dictionary mapping project ID to ProjectInfo
        """
        projects = {}
        include_subgroups = self.config.groups.include_subgroups

        # Fetch from groups by ID
        for group_id in self.config.groups.by_id:
            logger.info(
                f"Fetching projects from group ID {group_id} "
                f"(include_subgroups={include_subgroups})"
            )
            try:
                group_projects = self.client.list_group_projects(
                    group_id,
                    include_subgroups=include_subgroups
                )
                for proj_data in group_projects:
                    project_info = self._parse_project_data(proj_data)
                    projects[project_info.id] = project_info
                logger.info(f"Found {len(group_projects)} projects in group {group_id}")
            except GitLabNotFound:
                logger.warning(f"Group with ID {group_id} not found or not accessible")
            except GitLabAPIError as e:
                logger.error(f"Failed to fetch projects from group {group_id}: {e}")
                raise

        # Fetch from groups by path
        for group_path in self.config.groups.by_path:
            logger.info(
                f"Fetching projects from group path '{group_path}' "
                f"(include_subgroups={include_subgroups})"
            )
            try:
                group_projects = self.client.list_group_projects(
                    group_path,
                    include_subgroups=include_subgroups
                )
                for proj_data in group_projects:
                    project_info = self._parse_project_data(proj_data)
                    projects[project_info.id] = project_info
                logger.info(
                    f"Found {len(group_projects)} projects in group '{group_path}'"
                )
            except GitLabNotFound:
                logger.warning(
                    f"Group with path '{group_path}' not found or not accessible"
                )
            except GitLabAPIError as e:
                logger.error(
                    f"Failed to fetch projects from group '{group_path}': {e}"
                )
                raise

        return projects

    def _get_explicit_projects(self) -> Dict[int, ProjectInfo]:
        """
        Get explicitly configured projects.

        Returns:
            Dictionary mapping project ID to ProjectInfo
        """
        projects = {}

        # Fetch projects by ID
        for project_id in self.config.projects.by_id:
            logger.info(f"Fetching project with ID {project_id}")
            try:
                proj_data = self.client.get_project_by_id(project_id)
                project_info = self._parse_project_data(proj_data)
                projects[project_info.id] = project_info
            except GitLabNotFound:
                logger.warning(f"Project with ID {project_id} not found or not accessible")
            except GitLabAPIError as e:
                logger.error(f"Failed to fetch project {project_id}: {e}")
                raise

        # Fetch projects by path
        for project_path in self.config.projects.by_path:
            logger.info(f"Fetching project with path '{project_path}'")
            try:
                proj_data = self.client.get_project_by_path(project_path)
                project_info = self._parse_project_data(proj_data)
                projects[project_info.id] = project_info
            except GitLabNotFound:
                logger.warning(
                    f"Project with path '{project_path}' not found or not accessible"
                )
            except GitLabAPIError as e:
                logger.error(f"Failed to fetch project '{project_path}': {e}")
                raise

        return projects

    def _parse_project_data(self, proj_data: dict) -> ProjectInfo:
        """
        Parse project data from GitLab API response.

        Args:
            proj_data: Project data dictionary from API

        Returns:
            ProjectInfo object
        """
        return ProjectInfo(
            id=proj_data["id"],
            name=proj_data["name"],
            path_with_namespace=proj_data["path_with_namespace"],
            web_url=proj_data["web_url"],
        )

    def _apply_filters(self, projects: List[ProjectInfo]) -> List[ProjectInfo]:
        """
        Apply include/exclude filters to project list.

        Args:
            projects: List of projects to filter

        Returns:
            Filtered list of projects
        """
        include_paths = self.config.filters.include_project_paths
        exclude_paths = self.config.filters.exclude_project_paths

        # Apply include filter if specified
        if include_paths:
            include_set = set(include_paths)
            projects = [
                p for p in projects
                if p.path_with_namespace in include_set
            ]
            logger.info(
                f"Applied include filter: {len(projects)} projects match include list"
            )

        # Apply exclude filter
        if exclude_paths:
            exclude_set = set(exclude_paths)
            before_count = len(projects)
            projects = [
                p for p in projects
                if p.path_with_namespace not in exclude_set
            ]
            excluded_count = before_count - len(projects)
            if excluded_count > 0:
                logger.info(f"Excluded {excluded_count} projects via exclude filter")

        return projects


def resolve_projects(config: AppConfig, client: GitLabClient) -> List[ProjectInfo]:
    """
    Convenience function to resolve projects.

    Args:
        config: Application configuration
        client: GitLab API client

    Returns:
        List of ProjectInfo objects
    """
    resolver = ProjectResolver(config, client)
    return resolver.resolve_projects()

