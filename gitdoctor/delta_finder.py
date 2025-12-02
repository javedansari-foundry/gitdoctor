"""
Delta finder module.

Discovers the delta (difference) between two references (tags/branches/commits)
across multiple GitLab projects.
"""

import logging
from typing import List, Optional
from datetime import datetime

from .api_client import GitLabClient, GitLabNotFound, GitLabAPIError
from .project_resolver import ProjectInfo
from .models import DeltaCommit, DeltaResult, DeltaSummary


logger = logging.getLogger(__name__)


class DeltaFinder:
    """
    Discovers deltas between two references across multiple GitLab projects.
    
    For each project:
    1. Verifies both BASE and TARGET refs exist (can be tags, branches, or commits)
    2. Fetches all commits from both refs using paginated API
    3. Computes set difference (target_commits - base_commits) for exact delta
    4. Optionally filters by date range
    5. Gathers statistics
    
    Uses set difference algorithm instead of GitLab's compare API to avoid
    timeouts with large repositories. This approach is 100% accurate for any
    git history shape (merges, complex branching) and handles unlimited commit ranges.
    """

    def __init__(self, client: GitLabClient, projects: List[ProjectInfo]):
        """
        Initialize delta finder.

        Args:
            client: GitLab API client
            projects: List of projects to compare
        """
        self.client = client
        self.projects = projects

    def find_deltas(
        self,
        base_ref: str,
        target_ref: str,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> List[DeltaResult]:
        """
        Find deltas between base_ref and target_ref across all projects.
        
        This is the main entry point for delta discovery.
        
        Args:
            base_ref: Starting reference (e.g., "MobiquityPay_vX.10.15.2_PVG.B1")
            target_ref: Ending reference (e.g., "MobiquityPay_v11.0.0_20250908_PVG.B1")
            after_date: Optional ISO 8601 date - only include commits after this
            before_date: Optional ISO 8601 date - only include commits before this
            
        Returns:
            List of DeltaResult objects, one per project
            
        Example:
            >>> finder = DeltaFinder(client, projects)
            >>> deltas = finder.find_deltas("v1.0.0", "v2.0.0")
            >>> for delta in deltas:
            ...     if delta.has_changes:
            ...         print(f"{delta.project_path}: {len(delta.commits)} commits")
        """
        results = []
        
        logger.info(
            f"Finding delta from '{base_ref}' to '{target_ref}' "
            f"across {len(self.projects)} projects"
        )
        
        if after_date:
            logger.info(f"  Filtering commits after: {after_date}")
        if before_date:
            logger.info(f"  Filtering commits before: {before_date}")
        
        for i, project in enumerate(self.projects, 1):
            logger.info(
                f"[{i}/{len(self.projects)}] Comparing in "
                f"{project.path_with_namespace}"
            )
            
            delta = self._compare_in_project(
                project, base_ref, target_ref, after_date, before_date
            )
            results.append(delta)
            
            if delta.has_changes:
                logger.info(f"  ✓ Found {len(delta.commits)} commits")
            elif delta.error:
                logger.warning(f"  ✗ Error: {delta.error}")
            elif not delta.base_exists:
                logger.info(f"  ⊘ Base ref '{base_ref}' not found (skipped)")
            elif not delta.target_exists:
                logger.info(f"  ⊘ Target ref '{target_ref}' not found (skipped)")
            elif delta.compare_same_ref:
                logger.info("  = Refs are identical (no changes)")
            else:
                logger.info("  ○ No commits between refs")
        
        logger.info(
            f"Delta discovery complete. "
            f"Found changes in {sum(1 for d in results if d.has_changes)} projects."
        )
        
        return results

    def _compare_in_project(
        self,
        project: ProjectInfo,
        base_ref: str,
        target_ref: str,
        after_date: Optional[str],
        before_date: Optional[str]
    ) -> DeltaResult:
        """
        Compare two refs in a single project using set difference algorithm.
        
        This method fetches all commits from both refs using paginated API,
        then computes the set difference to find commits in target but not in base.
        This approach avoids timeouts and handles any git history shape accurately.
        
        Args:
            project: Project to compare in
            base_ref: Starting reference
            target_ref: Ending reference
            after_date: Optional date filter (ISO 8601)
            before_date: Optional date filter (ISO 8601)
            
        Returns:
            DeltaResult with commits and metadata
        """
        result = DeltaResult(
            project_id=project.id,
            project_name=project.name,
            project_path=project.path_with_namespace,
            project_web_url=project.web_url,
            base_ref=base_ref,
            target_ref=target_ref
        )
        
        try:
            # Step 1: Verify base ref exists
            result.base_exists = self._ref_exists(project.id, base_ref)
            if not result.base_exists:
                result.error = f"Base ref '{base_ref}' not found in this project"
                return result
            
            # Step 2: Verify target ref exists
            result.target_exists = self._ref_exists(project.id, target_ref)
            if not result.target_exists:
                result.error = f"Target ref '{target_ref}' not found in this project"
                return result
            
            # Step 3: Fetch all commits from TARGET ref (paginated)
            logger.debug(f"Fetching commits from target ref '{target_ref}'...")
            target_commits = self.client.list_commits_from_ref(
                project.id, target_ref
            )
            
            # Build a map of SHA -> commit data for target commits
            target_commit_map = {
                commit.get("id"): commit for commit in target_commits
            }
            target_shas = set(target_commit_map.keys())
            logger.debug(f"Found {len(target_shas)} commits in target ref")
            
            # Step 4: Fetch all commits from BASE ref (paginated)
            logger.debug(f"Fetching commits from base ref '{base_ref}'...")
            base_commits = self.client.list_commits_from_ref(
                project.id, base_ref
            )
            
            base_shas = {commit.get("id") for commit in base_commits}
            logger.debug(f"Found {len(base_shas)} commits in base ref")
            
            # Store commit counts for transparency
            result.base_commit_count = len(base_shas)
            result.target_commit_count = len(target_shas)
            
            # Step 5: Compute set difference (commits in target but not in base)
            delta_shas = target_shas - base_shas
            logger.debug(f"Delta contains {len(delta_shas)} commits")
            logger.info(f"  Base ref has {result.base_commit_count} commits, Target ref has {result.target_commit_count} commits")
            
            # Check if refs are identical
            if not delta_shas and target_shas == base_shas:
                result.compare_same_ref = True
            
            result.total_commits = len(delta_shas)
            
            # Step 6: Process delta commits with optional date filtering
            for sha in delta_shas:
                commit_data = target_commit_map[sha]
                committed_date = commit_data.get("committed_date", "")
                
                # Apply date filters if specified
                if after_date and committed_date and committed_date < after_date:
                    continue
                if before_date and committed_date and committed_date > before_date:
                    continue
                
                # Create DeltaCommit object
                delta_commit = DeltaCommit(
                    commit_sha=commit_data.get("id", ""),
                    short_id=commit_data.get("short_id", ""),
                    title=commit_data.get("title", ""),
                    message=commit_data.get("message", ""),
                    author_name=commit_data.get("author_name", ""),
                    author_email=commit_data.get("author_email", ""),
                    authored_date=commit_data.get("authored_date", ""),
                    committed_date=committed_date,
                    committer_name=commit_data.get("committer_name", ""),
                    committer_email=commit_data.get("committer_email", ""),
                    parent_ids=commit_data.get("parent_ids", []),
                    web_url=commit_data.get("web_url", "")
                )
                result.commits.append(delta_commit)
            
            # Sort commits by date (newest first) for consistent output
            result.commits.sort(key=lambda c: c.committed_date, reverse=True)
            
            # Note: Set difference approach doesn't provide diff stats
            # We'd need additional API calls to get file change details
            result.files_changed = 0
            result.total_additions = 0
            result.total_deletions = 0
            
        except GitLabNotFound as e:
            result.error = f"Resource not found: {str(e)}"
            logger.debug(f"GitLabNotFound in {project.path_with_namespace}: {e}")
        except GitLabAPIError as e:
            result.error = f"API error: {str(e)}"
            logger.error(
                f"GitLabAPIError in {project.path_with_namespace}: {e}"
            )
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
            logger.error(
                f"Unexpected error in {project.path_with_namespace}: {e}",
                exc_info=True
            )
        
        return result

    def _ref_exists(self, project_id: int, ref: str) -> bool:
        """
        Check if a reference (tag/branch/commit) exists in a project.
        
        Tries in order:
        1. Tag
        2. Branch  
        3. Commit SHA
        
        Args:
            project_id: GitLab project ID
            ref: Reference name to check
            
        Returns:
            True if ref exists, False otherwise
        """
        # Try as tag first
        try:
            self.client.get_tag(project_id, ref)
            logger.debug(f"Ref '{ref}' exists as tag in project {project_id}")
            return True
        except GitLabNotFound:
            pass
        except GitLabAPIError as e:
            logger.warning(f"Error checking tag '{ref}': {e}")
        
        # Try as branch
        try:
            self.client.get_branch(project_id, ref)
            logger.debug(f"Ref '{ref}' exists as branch in project {project_id}")
            return True
        except GitLabNotFound:
            pass
        except GitLabAPIError as e:
            logger.warning(f"Error checking branch '{ref}': {e}")
        
        # Try as commit SHA
        try:
            self.client.get_commit(project_id, ref)
            logger.debug(f"Ref '{ref}' exists as commit in project {project_id}")
            return True
        except GitLabNotFound:
            logger.debug(f"Ref '{ref}' not found in project {project_id}")
            return False
        except GitLabAPIError as e:
            logger.warning(f"Error checking commit '{ref}': {e}")
            return False

    def generate_summary(self, deltas: List[DeltaResult]) -> DeltaSummary:
        """
        Generate summary statistics from delta results.
        
        Args:
            deltas: List of DeltaResult objects
            
        Returns:
            DeltaSummary with aggregated statistics
        """
        if not deltas:
            return DeltaSummary(
                base_ref="",
                target_ref="",
                total_projects=0,
                projects_with_changes=0,
                projects_without_changes=0,
                projects_with_errors=0,
                total_commits=0,
                total_files_changed=0,
                total_additions=0,
                total_deletions=0
            )
        
        base_ref = deltas[0].base_ref
        target_ref = deltas[0].target_ref
        
        projects_with_changes = sum(1 for d in deltas if d.has_changes)
        projects_with_errors = sum(1 for d in deltas if d.error is not None)
        projects_without_changes = len(deltas) - projects_with_changes - projects_with_errors
        
        total_commits = sum(len(d.commits) for d in deltas)
        total_files_changed = sum(d.files_changed for d in deltas)
        total_additions = sum(d.total_additions for d in deltas)
        total_deletions = sum(d.total_deletions for d in deltas)
        
        # Aggregate commit counts from refs
        total_base_commits = sum(d.base_commit_count for d in deltas)
        total_target_commits = sum(d.target_commit_count for d in deltas)
        
        # Collect unique authors
        all_authors = set()
        for delta in deltas:
            for commit in delta.commits:
                all_authors.add(commit.author_name)
        
        # Get top projects by commit count
        project_commits = [
            (d.project_path, len(d.commits))
            for d in deltas if d.has_changes
        ]
        project_commits.sort(key=lambda x: x[1], reverse=True)
        
        return DeltaSummary(
            base_ref=base_ref,
            target_ref=target_ref,
            total_projects=len(deltas),
            projects_with_changes=projects_with_changes,
            projects_without_changes=projects_without_changes,
            projects_with_errors=projects_with_errors,
            total_base_commits=total_base_commits,
            total_target_commits=total_target_commits,
            total_commits=total_commits,
            total_files_changed=total_files_changed,
            total_additions=total_additions,
            total_deletions=total_deletions,
            unique_authors=sorted(list(all_authors)),
            top_projects=project_commits[:10]  # Top 10
        )

