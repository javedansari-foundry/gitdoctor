"""
Tests for configuration loading and validation.
"""

import pytest
import tempfile
from pathlib import Path

from gitdoctor.config import (
    load_config,
    ConfigError,
    AppConfig,
    GitLabConfig,
    ScanConfig,
)


def test_load_minimal_auto_discover_config():
    """Test loading a minimal valid configuration in auto_discover mode."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"
  private_token: "test-token-123"

scan:
  mode: "auto_discover"

groups:
  by_path:
    - "test-group"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        config = load_config(f.name)
        
        assert config.gitlab.base_url == "https://gitlab.example.com"
        assert config.gitlab.private_token == "test-token-123"
        assert config.gitlab.api_version == "v4"
        assert config.gitlab.verify_ssl is True
        assert config.scan.mode == "auto_discover"
        assert config.groups.by_path == ["test-group"]
        
        Path(f.name).unlink()


def test_load_minimal_explicit_config():
    """Test loading a minimal valid configuration in explicit mode."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"
  private_token: "test-token-123"

scan:
  mode: "explicit"

projects:
  by_id:
    - 123
    - 456
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        config = load_config(f.name)
        
        assert config.scan.mode == "explicit"
        assert config.projects.by_id == [123, 456]
        
        Path(f.name).unlink()


def test_load_full_config_with_filters():
    """Test loading a complete configuration with all options."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com/"
  private_token: "test-token-123"
  api_version: "v4"
  verify_ssl: false
  timeout_seconds: 30

scan:
  mode: "auto_discover"

projects:
  by_id:
    - 100
  by_path:
    - "group/project1"

groups:
  include_subgroups: false
  by_id:
    - 50
  by_path:
    - "test-group"

filters:
  include_project_paths:
    - "group/project1"
    - "group/project2"
  exclude_project_paths:
    - "group/excluded-project"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        config = load_config(f.name)
        
        # Test GitLab config (note: trailing slash should be removed)
        assert config.gitlab.base_url == "https://gitlab.example.com"
        assert config.gitlab.verify_ssl is False
        assert config.gitlab.timeout_seconds == 30
        
        # Test scan config
        assert config.scan.mode == "auto_discover"
        
        # Test projects
        assert config.projects.by_id == [100]
        assert config.projects.by_path == ["group/project1"]
        
        # Test groups
        assert config.groups.include_subgroups is False
        assert config.groups.by_id == [50]
        assert config.groups.by_path == ["test-group"]
        
        # Test filters
        assert len(config.filters.include_project_paths) == 2
        assert len(config.filters.exclude_project_paths) == 1
        
        Path(f.name).unlink()


def test_missing_required_base_url():
    """Test that missing base_url raises ConfigError."""
    config_content = """
gitlab:
  private_token: "test-token"

scan:
  mode: "auto_discover"

groups:
  by_path:
    - "test-group"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ConfigError, match="base_url"):
            load_config(f.name)
        
        Path(f.name).unlink()


def test_missing_required_token():
    """Test that missing private_token raises ConfigError."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"

scan:
  mode: "auto_discover"

groups:
  by_path:
    - "test-group"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ConfigError, match="private_token"):
            load_config(f.name)
        
        Path(f.name).unlink()


def test_invalid_scan_mode():
    """Test that invalid scan mode raises ConfigError."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"
  private_token: "test-token"

scan:
  mode: "invalid_mode"

groups:
  by_path:
    - "test-group"
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ConfigError, match="scan.mode"):
            load_config(f.name)
        
        Path(f.name).unlink()


def test_auto_discover_mode_requires_groups():
    """Test that auto_discover mode requires at least one group."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"
  private_token: "test-token"

scan:
  mode: "auto_discover"

groups:
  by_path: []
  by_id: []
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ConfigError, match="auto_discover mode"):
            load_config(f.name)
        
        Path(f.name).unlink()


def test_explicit_mode_requires_projects():
    """Test that explicit mode requires at least one project."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"
  private_token: "test-token"

scan:
  mode: "explicit"

projects:
  by_path: []
  by_id: []
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ConfigError, match="explicit mode"):
            load_config(f.name)
        
        Path(f.name).unlink()


def test_config_file_not_found():
    """Test that missing config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent-config.yaml")


def test_empty_config_file():
    """Test that empty config file raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        f.flush()
        
        with pytest.raises(ConfigError, match="empty"):
            load_config(f.name)
        
        Path(f.name).unlink()


def test_malformed_yaml():
    """Test that malformed YAML raises ConfigError."""
    config_content = """
gitlab:
  base_url: "https://gitlab.example.com"
  private_token: "test-token"
  invalid: yaml: content: here
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        with pytest.raises(ConfigError, match="parse YAML"):
            load_config(f.name)
        
        Path(f.name).unlink()

