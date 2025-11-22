"""
GitLab API client module.

Provides a wrapper around the GitLab v4 API with error handling and pagination support.
"""

from typing import Dict, List, Any, Optional
from urllib.parse import quote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GitLabAPIError(Exception):
    """Base exception for GitLab API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class GitLabNotFound(GitLabAPIError):
    """Raised when a resource is not found (404)."""
    pass


class GitLabUnauthorized(GitLabAPIError):
    """Raised when authentication fails (401)."""
    pass


class GitLabForbidden(GitLabAPIError):
    """Raised when access is forbidden (403)."""
    pass


class GitLabClient:
    """
    Client for interacting with GitLab API v4.
    
    Handles authentication, pagination, error handling, and provides
    convenient methods for common operations.
    """

    def __init__(
        self,
        base_url: str,
        private_token: str,
        api_version: str = "v4",
        verify_ssl: bool = True,
        timeout_seconds: int = 15,
    ):
        """
        Initialize GitLab API client.

        Args:
            base_url: GitLab instance base URL (e.g., https://gitlab.example.com)
            private_token: GitLab personal access token
            api_version: API version (default: v4)
            verify_ssl: Whether to verify SSL certificates
            timeout_seconds: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/{api_version}"
        self.private_token = private_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout_seconds

        # Create session with retry logic
        self.session = requests.Session()
        
        # Configure retries for connection errors and specific HTTP codes
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            "PRIVATE-TOKEN": self.private_token,
            "Content-Type": "application/json",
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request to the GitLab API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            GitLabAPIError: For various API errors
        """
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle specific HTTP status codes
            if response.status_code == 401:
                raise GitLabUnauthorized(
                    "Authentication failed. Check your private token.",
                    status_code=401
                )
            elif response.status_code == 403:
                raise GitLabForbidden(
                    "Access forbidden. Check your permissions.",
                    status_code=403
                )
            elif response.status_code == 404:
                raise GitLabNotFound(
                    f"Resource not found: {endpoint}",
                    status_code=404
                )
            elif not response.ok:
                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += f" - {error_data['message']}"
                except:
                    error_msg += f" - {response.text[:200]}"
                raise GitLabAPIError(error_msg, status_code=response.status_code)
            
            return response

        except requests.exceptions.Timeout:
            raise GitLabAPIError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.SSLError as e:
            raise GitLabAPIError(f"SSL verification failed: {e}")
        except requests.exceptions.ConnectionError as e:
            raise GitLabAPIError(f"Connection failed: {e}")
        except (GitLabAPIError, GitLabNotFound, GitLabUnauthorized, GitLabForbidden):
            raise
        except Exception as e:
            raise GitLabAPIError(f"Unexpected error: {e}")

    def _get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages of a paginated API endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters
            per_page: Items per page (max 100)

        Returns:
            List of all items across all pages
        """
        if params is None:
            params = {}
        
        params["per_page"] = min(per_page, 100)
        params["page"] = 1
        
        all_items = []
        
        while True:
            response = self._make_request("GET", endpoint, params=params)
            items = response.json()
            
            if not items:
                break
            
            all_items.extend(items)
            
            # Check if there are more pages
            if "x-next-page" in response.headers and response.headers["x-next-page"]:
                params["page"] = int(response.headers["x-next-page"])
            else:
                break
        
        return all_items

    def get_project_by_id(self, project_id: int) -> Dict[str, Any]:
        """
        Get project details by project ID.

        Args:
            project_id: GitLab project ID

        Returns:
            Project data dictionary

        Raises:
            GitLabNotFound: If project doesn't exist
            GitLabAPIError: For other API errors
        """
        endpoint = f"projects/{project_id}"
        response = self._make_request("GET", endpoint)
        return response.json()

    def get_project_by_path(self, path: str) -> Dict[str, Any]:
        """
        Get project details by project path.

        Args:
            path: Project path (e.g., "group/subgroup/project")

        Returns:
            Project data dictionary

        Raises:
            GitLabNotFound: If project doesn't exist
            GitLabAPIError: For other API errors
        """
        encoded_path = quote(path, safe="")
        endpoint = f"projects/{encoded_path}"
        response = self._make_request("GET", endpoint)
        return response.json()

    def list_group_projects(
        self,
        group_id_or_path: str | int,
        include_subgroups: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all projects in a group.

        Args:
            group_id_or_path: Group ID or path
            include_subgroups: Whether to include projects from subgroups

        Returns:
            List of project data dictionaries

        Raises:
            GitLabNotFound: If group doesn't exist
            GitLabAPIError: For other API errors
        """
        # Encode path if it's a string
        if isinstance(group_id_or_path, str):
            group_identifier = quote(group_id_or_path, safe="")
        else:
            group_identifier = str(group_id_or_path)
        
        endpoint = f"groups/{group_identifier}/projects"
        params = {
            "include_subgroups": str(include_subgroups).lower(),
            "archived": "false",  # Exclude archived projects by default
        }
        
        return self._get_paginated(endpoint, params=params)

    def get_commit(self, project_id: int, sha: str) -> Dict[str, Any]:
        """
        Get commit details.

        Args:
            project_id: GitLab project ID
            sha: Commit SHA

        Returns:
            Commit data dictionary

        Raises:
            GitLabNotFound: If commit doesn't exist in project
            GitLabAPIError: For other API errors
        """
        endpoint = f"projects/{project_id}/repository/commits/{sha}"
        response = self._make_request("GET", endpoint)
        return response.json()

    def list_commit_refs(
        self,
        project_id: int,
        sha: str,
        ref_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all branches and tags that contain a commit.

        Args:
            project_id: GitLab project ID
            sha: Commit SHA
            ref_type: Optional filter: "branch", "tag", or None for all

        Returns:
            List of reference data dictionaries with 'type' and 'name' fields

        Raises:
            GitLabNotFound: If commit doesn't exist
            GitLabAPIError: For other API errors
        """
        endpoint = f"projects/{project_id}/repository/commits/{sha}/refs"
        params = {}
        if ref_type:
            params["type"] = ref_type
        
        return self._get_paginated(endpoint, params=params)

    def test_connection(self) -> bool:
        """
        Test the connection to GitLab API.

        Returns:
            True if connection is successful

        Raises:
            GitLabAPIError: If connection fails
        """
        try:
            response = self._make_request("GET", "version")
            return response.ok
        except Exception as e:
            raise GitLabAPIError(f"Connection test failed: {e}")

