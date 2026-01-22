"""
GitLab API client module.

Provides a wrapper around the GitLab v4 API with error handling and pagination support.
"""
from __future__ import annotations

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

    def list_commits_from_ref(
        self,
        project_id: int,
        ref_name: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all commits reachable from a ref (branch/tag/commit) with pagination.
        
        This method fetches commits in pages to avoid timeouts with large repositories.
        Used for delta discovery via set difference algorithm.
        
        Args:
            project_id: GitLab project ID
            ref_name: Branch name, tag name, or commit SHA to list commits from
            since: Only commits after this date (ISO 8601 format, e.g., "2025-01-01T00:00:00Z")
            until: Only commits before this date (ISO 8601 format)
            per_page: Items per page (max 100)
        
        Returns:
            List of commit data dictionaries, each containing:
            - id: Full commit SHA
            - short_id: Short commit SHA
            - title: Commit title (first line of message)
            - message: Full commit message
            - author_name, author_email, authored_date
            - committer_name, committer_email, committed_date
            - parent_ids: List of parent commit SHAs
            - web_url: URL to view commit in GitLab
        
        Raises:
            GitLabNotFound: If project or ref doesn't exist
            GitLabAPIError: For other API errors
        
        Example:
            >>> commits = client.list_commits_from_ref(123, "v2.0.0")
            >>> print(f"Found {len(commits)} commits")
        """
        endpoint = f"projects/{project_id}/repository/commits"
        params = {
            "ref_name": ref_name,
        }
        
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        return self._get_paginated(endpoint, params=params, per_page=per_page)

    def compare_refs(
        self,
        project_id: int,
        from_ref: str,
        to_ref: str,
        straight: bool = True
    ) -> Dict[str, Any]:
        """
        Compare two refs (tags/branches/commits) in a project.
        
        DEPRECATED: This method uses GitLab's compare API which times out with
        large commit volumes. Use list_commits_from_ref() with set difference
        algorithm instead for reliable delta discovery.
        
        Args:
            project_id: GitLab project ID
            from_ref: Starting reference (base tag/branch/commit)
            to_ref: Ending reference (target tag/branch/commit)
            straight: If True, compare directly. If False, find merge base first.
        
        Returns:
            Dictionary containing:
            - commits: List of commit objects
            - diffs: List of file changes
            - compare_timeout: Boolean indicating if comparison timed out
            - compare_same_ref: Boolean indicating if refs are identical
        
        Raises:
            GitLabNotFound: If project or refs don't exist
            GitLabAPIError: For other API errors
        """
        endpoint = f"projects/{project_id}/repository/compare"
        params = {
            "from": from_ref,
            "to": to_ref,
            "straight": str(straight).lower()  # Convert to "true"/"false"
        }
        
        response = self._make_request("GET", endpoint, params=params)
        return response.json()

    def get_tag(self, project_id: int, tag_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tag.
        
        Args:
            project_id: GitLab project ID
            tag_name: Name of the tag
        
        Returns:
            Dictionary with tag information including:
            - name: Tag name
            - message: Tag message
            - target: Commit SHA the tag points to
            - commit: Commit details
            - release: Release information if any
        
        Raises:
            GitLabNotFound: If project or tag doesn't exist
            GitLabAPIError: For other API errors
        """
        # URL encode the tag name to handle special characters
        encoded_tag = quote(tag_name, safe='')
        endpoint = f"projects/{project_id}/repository/tags/{encoded_tag}"
        
        response = self._make_request("GET", endpoint)
        return response.json()

    def get_branch(self, project_id: int, branch_name: str) -> Dict[str, Any]:
        """
        Get information about a specific branch.
        
        Args:
            project_id: GitLab project ID
            branch_name: Name of the branch
        
        Returns:
            Dictionary with branch information including:
            - name: Branch name
            - commit: Latest commit details
            - merged: Whether branch is merged
            - protected: Whether branch is protected
            - developers_can_push: Push permissions
            - developers_can_merge: Merge permissions
        
        Raises:
            GitLabNotFound: If project or branch doesn't exist
            GitLabAPIError: For other API errors
        """
        # URL encode the branch name to handle special characters (e.g., "feature/my-branch")
        encoded_branch = quote(branch_name, safe='')
        endpoint = f"projects/{project_id}/repository/branches/{encoded_branch}"
        
        response = self._make_request("GET", endpoint)
        return response.json()

    def list_merge_requests(
        self,
        project_id: int,
        state: str = "merged",
        target_branch: Optional[str] = None,
        source_branch: Optional[str] = None,
        merged_after: Optional[str] = None,
        merged_before: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List merge requests for a project with various filters.
        
        Args:
            project_id: GitLab project ID
            state: MR state filter - 'opened', 'closed', 'merged', 'all' (default: 'merged')
            target_branch: Filter by target branch name
            source_branch: Filter by source branch name
            merged_after: Only MRs merged after this date (ISO 8601 format)
            merged_before: Only MRs merged before this date (ISO 8601 format)
            created_after: Only MRs created after this date (ISO 8601 format)
            created_before: Only MRs created before this date (ISO 8601 format)
            per_page: Items per page (max 100)
        
        Returns:
            List of merge request data dictionaries, each containing:
            - id: MR ID (internal)
            - iid: MR IID (visible in GitLab UI)
            - title: MR title
            - description: MR description
            - state: MR state (merged, opened, closed)
            - source_branch: Source branch name
            - target_branch: Target branch name
            - author: Author info dict
            - merged_by: Who merged it (if merged)
            - merged_at: When it was merged (if merged)
            - created_at: When it was created
            - updated_at: When it was last updated
            - web_url: URL to view MR in GitLab
            - sha: The merge commit SHA (if merged)
        
        Raises:
            GitLabNotFound: If project doesn't exist
            GitLabAPIError: For other API errors
        
        Example:
            >>> mrs = client.list_merge_requests(
            ...     123,
            ...     state="merged",
            ...     target_branch="master",
            ...     merged_after="2025-10-01T00:00:00Z"
            ... )
            >>> print(f"Found {len(mrs)} merged MRs to master")
        """
        endpoint = f"projects/{project_id}/merge_requests"
        params = {
            "state": state,
        }
        
        if target_branch:
            params["target_branch"] = target_branch
        if source_branch:
            params["source_branch"] = source_branch
        if merged_after:
            params["merged_after"] = merged_after
        if merged_before:
            params["merged_before"] = merged_before
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        
        return self._get_paginated(endpoint, params=params, per_page=per_page)

    def get_merge_request(
        self,
        project_id: int,
        mr_iid: int
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific merge request.
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID (the visible number in GitLab)
        
        Returns:
            Dictionary with merge request details
        
        Raises:
            GitLabNotFound: If project or MR doesn't exist
            GitLabAPIError: For other API errors
        """
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}"
        response = self._make_request("GET", endpoint)
        return response.json()

    def get_commit_diff(self, project_id: int, sha: str) -> List[Dict[str, Any]]:
        """
        Get file diffs for a specific commit.
        
        Args:
            project_id: GitLab project ID
            sha: Commit SHA
        
        Returns:
            List of changed files with diff information, each containing:
            - old_path: Path before change
            - new_path: Path after change
            - diff: Unified diff text
            - new_file: Boolean, true if file was created
            - deleted_file: Boolean, true if file was deleted
            - renamed_file: Boolean, true if file was renamed
            - a_mode: File mode before change
            - b_mode: File mode after change
        
        Raises:
            GitLabNotFound: If commit doesn't exist
            GitLabAPIError: For other API errors
        
        Example:
            >>> diffs = client.get_commit_diff(123, "abc123...")
            >>> for file_diff in diffs:
            ...     print(f"Changed: {file_diff['new_path']}")
        """
        endpoint = f"projects/{project_id}/repository/commits/{sha}/diff"
        return self._get_paginated(endpoint)

    def get_merge_request_commits(
        self,
        project_id: int,
        mr_iid: int
    ) -> List[Dict[str, Any]]:
        """
        Get all commits that are part of a merge request.
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID (the visible number in GitLab)
        
        Returns:
            List of commit data dictionaries, each containing:
            - id: Full commit SHA
            - short_id: Short commit SHA
            - title: Commit title
            - message: Full commit message
            - author_name, author_email
            - created_at: Commit date
            - web_url: URL to view commit
        
        Raises:
            GitLabNotFound: If project or MR doesn't exist
            GitLabAPIError: For other API errors
        
        Example:
            >>> commits = client.get_merge_request_commits(123, 456)
            >>> print(f"MR has {len(commits)} commits")
        """
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/commits"
        return self._get_paginated(endpoint)

    def get_merge_request_changes(
        self,
        project_id: int,
        mr_iid: int
    ) -> Dict[str, Any]:
        """
        Get complete changeset (MR details + all file changes) for a merge request.
        
        This returns the full MR data plus a 'changes' array containing all file
        diffs across all commits in the MR.
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request IID (the visible number in GitLab)
        
        Returns:
            Dictionary containing:
            - All standard MR fields (id, iid, title, description, etc.)
            - changes: List of file changes with diffs
              Each change contains:
              - old_path, new_path: File paths
              - diff: Unified diff text
              - new_file, deleted_file, renamed_file: Boolean flags
        
        Raises:
            GitLabNotFound: If project or MR doesn't exist
            GitLabAPIError: For other API errors
        
        Example:
            >>> mr_data = client.get_merge_request_changes(123, 456)
            >>> print(f"Title: {mr_data['title']}")
            >>> print(f"Changed files: {len(mr_data['changes'])}")
        """
        endpoint = f"projects/{project_id}/merge_requests/{mr_iid}/changes"
        response = self._make_request("GET", endpoint)
        return response.json()

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

