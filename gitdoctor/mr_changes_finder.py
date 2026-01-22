"""
MR Changes Finder module.

Fetches complete changeset for merge requests including:
- All commits in the MR
- All file changes with diffs
- JIRA ticket references
- Metadata for intelligent test selection
"""
from __future__ import annotations

import logging
from typing import Optional

from .api_client import GitLabClient, GitLabAPIError, GitLabNotFound
from .models import MRChangesResult, CommitChange, FileChange
from .jira_integration import JIRALinker


logger = logging.getLogger(__name__)


class MRChangesFinder:
    """
    Fetches complete changeset information for merge requests.
    
    This is designed for intelligent test selection - provides all the data
    needed to determine which tests should run based on MR changes.
    """
    
    def __init__(
        self,
        client: GitLabClient,
        jira_linker: Optional[JIRALinker] = None
    ):
        """
        Initialize MR changes finder.
        
        Args:
            client: GitLab API client instance
            jira_linker: Optional JIRA linker for extracting ticket references
        """
        self.client = client
        self.jira_linker = jira_linker
    
    def get_mr_changes(
        self,
        project_id_or_path: str | int,
        mr_iid: int,
        include_diffs: bool = True
    ) -> MRChangesResult:
        """
        Get complete changeset for a merge request.
        
        Args:
            project_id_or_path: Project ID (int) or path (str like 'group/project')
            mr_iid: Merge request IID (the visible MR number)
            include_diffs: Whether to include full diff text (default: True)
        
        Returns:
            MRChangesResult with all MR data, commits, and file changes
        
        Example:
            >>> finder = MRChangesFinder(client)
            >>> result = finder.get_mr_changes(123, 456)
            >>> print(f"MR Title: {result.title}")
            >>> print(f"Commits: {result.total_commits}")
            >>> print(f"Files changed: {result.total_files_changed}")
            >>> for fc in result.get_non_test_files():
            ...     print(f"  - {fc.new_path}")
        """
        # Resolve project ID if path was provided
        if isinstance(project_id_or_path, str):
            try:
                project_data = self.client.get_project_by_path(project_id_or_path)
                project_id = project_data['id']
                project_name = project_data['name']
                project_path = project_data['path_with_namespace']
                project_web_url = project_data['web_url']
            except GitLabNotFound:
                return MRChangesResult(
                    project_id=0,
                    project_name="",
                    project_path=project_id_or_path,
                    project_web_url="",
                    mr_iid=mr_iid,
                    mr_id=0,
                    title="",
                    description="",
                    state="",
                    source_branch="",
                    target_branch="",
                    author_name="",
                    author_username="",
                    error=f"Project not found: {project_id_or_path}"
                )
        else:
            project_id = project_id_or_path
            try:
                project_data = self.client.get_project_by_id(project_id)
                project_name = project_data['name']
                project_path = project_data['path_with_namespace']
                project_web_url = project_data['web_url']
            except GitLabNotFound:
                return MRChangesResult(
                    project_id=project_id,
                    project_name="",
                    project_path="",
                    project_web_url="",
                    mr_iid=mr_iid,
                    mr_id=0,
                    title="",
                    description="",
                    state="",
                    source_branch="",
                    target_branch="",
                    author_name="",
                    author_username="",
                    error=f"Project not found: {project_id}"
                )
        
        logger.info(f"Fetching MR !{mr_iid} from {project_path} (ID: {project_id})")
        
        try:
            # Step 1: Get MR metadata and file changes
            logger.info(f"  Fetching MR changes...")
            mr_data = self.client.get_merge_request_changes(project_id, mr_iid)
            
            # Extract MR metadata
            author = mr_data.get('author', {}) or {}
            merged_by = mr_data.get('merged_by', {}) or {}
            
            result = MRChangesResult(
                project_id=project_id,
                project_name=project_name,
                project_path=project_path,
                project_web_url=project_web_url,
                mr_iid=mr_data.get('iid', mr_iid),
                mr_id=mr_data.get('id', 0),
                title=mr_data.get('title', ''),
                description=mr_data.get('description', '') or '',
                state=mr_data.get('state', ''),
                source_branch=mr_data.get('source_branch', ''),
                target_branch=mr_data.get('target_branch', ''),
                author_name=author.get('name', 'Unknown'),
                author_username=author.get('username', 'unknown'),
                merged_by_name=merged_by.get('name') if merged_by else None,
                merged_at=mr_data.get('merged_at'),
                created_at=mr_data.get('created_at', ''),
                web_url=mr_data.get('web_url', ''),
                merge_commit_sha=mr_data.get('merge_commit_sha'),
                labels=mr_data.get('labels', []) or []
            )
            
            # Extract JIRA tickets from MR title and description
            all_jira_tickets = []
            if self.jira_linker:
                all_jira_tickets.extend(
                    self.jira_linker.extract_tickets_from_message(result.title)
                )
                all_jira_tickets.extend(
                    self.jira_linker.extract_tickets_from_message(result.description)
                )
            
            # Step 2: Parse file changes from MR
            logger.info(f"  Parsing file changes...")
            file_changes = []
            for change in mr_data.get('changes', []):
                fc = FileChange(
                    old_path=change.get('old_path', ''),
                    new_path=change.get('new_path', ''),
                    diff=change.get('diff', '') if include_diffs else '',
                    new_file=change.get('new_file', False),
                    deleted_file=change.get('deleted_file', False),
                    renamed_file=change.get('renamed_file', False),
                    a_mode=change.get('a_mode'),
                    b_mode=change.get('b_mode')
                )
                file_changes.append(fc)
            
            result.all_file_changes = file_changes
            logger.info(f"  Found {len(file_changes)} file changes")
            
            # Step 3: Get all commits in the MR
            logger.info(f"  Fetching MR commits...")
            commits_data = self.client.get_merge_request_commits(project_id, mr_iid)
            logger.info(f"  Found {len(commits_data)} commits")
            
            # Step 4: For each commit, get its diffs and extract JIRA tickets
            commits = []
            for idx, commit_data in enumerate(commits_data, 1):
                commit_sha = commit_data['id']
                logger.debug(f"  [{idx}/{len(commits_data)}] Processing commit {commit_sha[:8]}...")
                
                # Get commit diffs
                try:
                    commit_diffs = self.client.get_commit_diff(project_id, commit_sha)
                    
                    # Parse commit diffs
                    commit_file_changes = []
                    for diff in commit_diffs:
                        fc = FileChange(
                            old_path=diff.get('old_path', ''),
                            new_path=diff.get('new_path', ''),
                            diff=diff.get('diff', '') if include_diffs else '',
                            new_file=diff.get('new_file', False),
                            deleted_file=diff.get('deleted_file', False),
                            renamed_file=diff.get('renamed_file', False),
                            a_mode=diff.get('a_mode'),
                            b_mode=diff.get('b_mode')
                        )
                        commit_file_changes.append(fc)
                    
                    # Extract JIRA tickets from commit message
                    commit_jira_tickets = []
                    if self.jira_linker:
                        commit_message = commit_data.get('message', '')
                        commit_jira_tickets = self.jira_linker.extract_tickets_from_message(commit_message)
                        all_jira_tickets.extend(commit_jira_tickets)
                    
                    # Create CommitChange object
                    commit_change = CommitChange(
                        commit_sha=commit_sha,
                        short_id=commit_data.get('short_id', commit_sha[:8]),
                        title=commit_data.get('title', ''),
                        message=commit_data.get('message', ''),
                        author_name=commit_data.get('author_name', ''),
                        author_email=commit_data.get('author_email', ''),
                        created_at=commit_data.get('created_at', ''),
                        web_url=commit_data.get('web_url', ''),
                        file_changes=commit_file_changes,
                        jira_tickets=commit_jira_tickets
                    )
                    commits.append(commit_change)
                    
                except GitLabAPIError as e:
                    logger.warning(f"  Failed to get diffs for commit {commit_sha[:8]}: {e}")
                    # Still add commit without diffs
                    commit_change = CommitChange(
                        commit_sha=commit_sha,
                        short_id=commit_data.get('short_id', commit_sha[:8]),
                        title=commit_data.get('title', ''),
                        message=commit_data.get('message', ''),
                        author_name=commit_data.get('author_name', ''),
                        author_email=commit_data.get('author_email', ''),
                        created_at=commit_data.get('created_at', ''),
                        web_url=commit_data.get('web_url', '')
                    )
                    commits.append(commit_change)
            
            result.commits = commits
            result.jira_tickets = all_jira_tickets
            
            # Log summary
            logger.info(f"✓ MR !{mr_iid} analysis complete:")
            logger.info(f"  - Commits: {result.total_commits}")
            logger.info(f"  - Files changed: {result.total_files_changed}")
            logger.info(f"  - JIRA tickets: {len(result.unique_jira_tickets)}")
            if result.unique_jira_tickets:
                logger.info(f"    {', '.join(result.unique_jira_tickets)}")
            
            return result
            
        except GitLabNotFound:
            error_msg = f"Merge request !{mr_iid} not found in project {project_path}"
            logger.error(f"✗ {error_msg}")
            return MRChangesResult(
                project_id=project_id,
                project_name=project_name,
                project_path=project_path,
                project_web_url=project_web_url,
                mr_iid=mr_iid,
                mr_id=0,
                title="",
                description="",
                state="",
                source_branch="",
                target_branch="",
                author_name="",
                author_username="",
                error=error_msg
            )
        
        except GitLabAPIError as e:
            error_msg = f"API error fetching MR !{mr_iid}: {e}"
            logger.error(f"✗ {error_msg}")
            return MRChangesResult(
                project_id=project_id,
                project_name=project_name,
                project_path=project_path,
                project_web_url=project_web_url,
                mr_iid=mr_iid,
                mr_id=0,
                title="",
                description="",
                state="",
                source_branch="",
                target_branch="",
                author_name="",
                author_username="",
                error=error_msg
            )
        
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"✗ {error_msg}", exc_info=True)
            return MRChangesResult(
                project_id=project_id,
                project_name=project_name,
                project_path=project_path,
                project_web_url=project_web_url,
                mr_iid=mr_iid,
                mr_id=0,
                title="",
                description="",
                state="",
                source_branch="",
                target_branch="",
                author_name="",
                author_username="",
                error=error_msg
            )

