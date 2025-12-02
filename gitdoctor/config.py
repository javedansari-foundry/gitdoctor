"""
Configuration module for GitDoctor.

Handles loading and validating YAML configuration files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid or missing required fields."""
    pass


@dataclass
class GitLabConfig:
    """GitLab connection configuration."""
    base_url: str
    private_token: str
    api_version: str = "v4"
    verify_ssl: bool = True
    timeout_seconds: int = 15

    def __post_init__(self):
        if not self.base_url:
            raise ConfigError("gitlab.base_url is required")
        if not self.private_token:
            raise ConfigError("gitlab.private_token is required")
        # Remove trailing slash from base_url if present
        self.base_url = self.base_url.rstrip("/")


@dataclass
class ProjectsConfig:
    """Configuration for explicitly specified projects."""
    by_id: List[int] = field(default_factory=list)
    by_path: List[str] = field(default_factory=list)


@dataclass
class GroupsConfig:
    """Configuration for GitLab groups to discover projects from."""
    include_subgroups: bool = True
    by_id: List[int] = field(default_factory=list)
    by_path: List[str] = field(default_factory=list)


@dataclass
class FiltersConfig:
    """Configuration for filtering which projects to search."""
    include_project_paths: List[str] = field(default_factory=list)
    exclude_project_paths: List[str] = field(default_factory=list)


@dataclass
class JIRAConfig:
    """Configuration for JIRA integration."""
    base_url: Optional[str] = None
    project_key: Optional[str] = None

    def __post_init__(self):
        if self.base_url:
            # Remove trailing slash if present
            self.base_url = self.base_url.rstrip("/")


@dataclass
class NotificationsConfig:
    """Configuration for notifications."""
    slack_webhook: Optional[str] = None
    teams_webhook: Optional[str] = None


@dataclass
class ScanConfig:
    """Configuration for scan mode."""
    mode: str = "auto_discover"  # "auto_discover" or "explicit"

    def __post_init__(self):
        valid_modes = ["auto_discover", "explicit"]
        if self.mode not in valid_modes:
            raise ConfigError(
                f"scan.mode must be one of {valid_modes}, got: {self.mode}"
            )


@dataclass
class AppConfig:
    """Main application configuration."""
    gitlab: GitLabConfig
    scan: ScanConfig
    projects: ProjectsConfig = field(default_factory=ProjectsConfig)
    groups: GroupsConfig = field(default_factory=GroupsConfig)
    filters: FiltersConfig = field(default_factory=FiltersConfig)
    jira: JIRAConfig = field(default_factory=JIRAConfig)
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)

    def __post_init__(self):
        # Validate that at least one source is configured
        if self.scan.mode == "auto_discover":
            if not self.groups.by_id and not self.groups.by_path:
                raise ConfigError(
                    "In auto_discover mode, at least one group must be configured "
                    "in groups.by_id or groups.by_path"
                )
        elif self.scan.mode == "explicit":
            if not self.projects.by_id and not self.projects.by_path:
                raise ConfigError(
                    "In explicit mode, at least one project must be configured "
                    "in projects.by_id or projects.by_path"
                )


def load_config(config_path: str | Path) -> AppConfig:
    """
    Load and validate configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        AppConfig: Validated application configuration

    Raises:
        ConfigError: If configuration is invalid or missing required fields
        FileNotFoundError: If configuration file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}")

    if not raw_config:
        raise ConfigError("Configuration file is empty")

    try:
        # Parse GitLab config
        gitlab_data = raw_config.get("gitlab", {})
        if not gitlab_data:
            raise ConfigError("gitlab section is required in configuration")
        
        gitlab_config = GitLabConfig(
            base_url=gitlab_data.get("base_url", ""),
            private_token=gitlab_data.get("private_token", ""),
            api_version=gitlab_data.get("api_version", "v4"),
            verify_ssl=gitlab_data.get("verify_ssl", True),
            timeout_seconds=gitlab_data.get("timeout_seconds", 15),
        )

        # Parse scan config
        scan_data = raw_config.get("scan", {})
        scan_config = ScanConfig(
            mode=scan_data.get("mode", "auto_discover")
        )

        # Parse projects config
        projects_data = raw_config.get("projects", {})
        projects_config = ProjectsConfig(
            by_id=projects_data.get("by_id", []),
            by_path=projects_data.get("by_path", []),
        )

        # Parse groups config
        groups_data = raw_config.get("groups", {})
        groups_config = GroupsConfig(
            include_subgroups=groups_data.get("include_subgroups", True),
            by_id=groups_data.get("by_id", []),
            by_path=groups_data.get("by_path", []),
        )

        # Parse filters config
        filters_data = raw_config.get("filters", {})
        filters_config = FiltersConfig(
            include_project_paths=filters_data.get("include_project_paths", []),
            exclude_project_paths=filters_data.get("exclude_project_paths", []),
        )

        # Parse JIRA config (optional)
        jira_data = raw_config.get("jira", {})
        jira_config = JIRAConfig(
            base_url=jira_data.get("base_url"),
            project_key=jira_data.get("project_key"),
        )

        # Parse notifications config (optional)
        notifications_data = raw_config.get("notifications", {})
        notifications_config = NotificationsConfig(
            slack_webhook=notifications_data.get("slack_webhook"),
            teams_webhook=notifications_data.get("teams_webhook"),
        )

        # Create and return main config
        return AppConfig(
            gitlab=gitlab_config,
            scan=scan_config,
            projects=projects_config,
            groups=groups_config,
            filters=filters_config,
            jira=jira_config,
            notifications=notifications_config,
        )

    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Failed to parse configuration: {e}")

