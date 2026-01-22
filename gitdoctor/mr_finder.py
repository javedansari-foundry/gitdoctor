"""
Merge Request finder module.

Finds and tracks merge requests across GitLab projects with various filters.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .api_client import GitLabClient, GitLabAPIError, GitLabNotFound
from .models import MergeRequest, MRResult, MRSummary


logger = logging.getLogger(__name__)


class MRFinder:
    """
    Finds and tracks merge requests across multiple GitLab projects.
    
    Supports filtering by:
    - Target branch (e.g., 'master', 'main')
    - Source branch (e.g., 'premaster', 'develop')
    - State ('merged', 'opened', 'closed', 'all')
    - Date range (merged_after/merged_before or created_after/created_before)
    """
    
    def __init__(self, client: GitLabClient, projects: List):
        """
        Initialize MR finder.
        
        Args:
            client: GitLab API client instance
            projects: List of ProjectInfo objects to search across
        """
        self.client = client
        self.projects = projects
    
    def find_merge_requests(
        self,
        target_branch: Optional[str] = None,
        source_branch: Optional[str] = None,
        state: str = "merged",
        merged_after: Optional[str] = None,
        merged_before: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> List[MRResult]:
        """
        Find merge requests across all configured projects.
        
        Args:
            target_branch: Filter by target branch (e.g., 'master')
            source_branch: Filter by source branch (e.g., 'premaster')
            state: MR state filter - 'merged', 'opened', 'closed', 'all'
            merged_after: Only MRs merged after this date (ISO 8601)
            merged_before: Only MRs merged before this date (ISO 8601)
            created_after: Only MRs created after this date (ISO 8601)
            created_before: Only MRs created before this date (ISO 8601)
        
        Returns:
            List of MRResult objects, one per project
        """
        results = []
        total_projects = len(self.projects)
        
        logger.info(f"Finding merge requests across {total_projects} projects")
        
        for idx, project in enumerate(self.projects, 1):
            logger.info(f"[{idx}/{total_projects}] Fetching MRs from {project.path_with_namespace}")
            
            result = self._fetch_project_mrs(
                project=project,
                target_branch=target_branch,
                source_branch=source_branch,
                state=state,
                merged_after=merged_after,
                merged_before=merged_before,
                created_after=created_after,
                created_before=created_before
            )
            results.append(result)
        
        # Log summary
        total_mrs = sum(r.total_mrs for r in results)
        projects_with_mrs = sum(1 for r in results if r.has_mrs)
        logger.info(f"MR fetch complete. Found {total_mrs} MRs in {projects_with_mrs} projects.")
        
        return results
    
    def _fetch_project_mrs(
        self,
        project,
        target_branch: Optional[str],
        source_branch: Optional[str],
        state: str,
        merged_after: Optional[str],
        merged_before: Optional[str],
        created_after: Optional[str],
        created_before: Optional[str]
    ) -> MRResult:
        """
        Fetch merge requests for a single project.
        
        Args:
            project: ProjectInfo object
            ... (same as find_merge_requests)
        
        Returns:
            MRResult object for this project
        """
        result = MRResult(
            project_id=project.id,
            project_name=project.name,
            project_path=project.path_with_namespace,
            project_web_url=project.web_url,
            target_branch=target_branch,
            source_branch=source_branch,
            state_filter=state
        )
        
        try:
            # Fetch MRs from GitLab API
            mr_data = self.client.list_merge_requests(
                project_id=project.id,
                state=state,
                target_branch=target_branch,
                source_branch=source_branch,
                merged_after=merged_after,
                merged_before=merged_before,
                created_after=created_after,
                created_before=created_before
            )
            
            # Convert API response to MergeRequest objects
            merge_requests = []
            for mr in mr_data:
                merge_requests.append(MergeRequest.from_api_response(mr))
            
            result.merge_requests = merge_requests
            result.total_mrs = len(merge_requests)
            
            if merge_requests:
                logger.info(f"  ✓ Found {len(merge_requests)} MRs")
            else:
                logger.debug(f"  No MRs found matching filters")
        
        except GitLabNotFound as e:
            logger.warning(f"  ✗ Project not found: {e}")
            result.error = f"Project not found: {e}"
        
        except GitLabAPIError as e:
            logger.error(f"  ✗ API error: {e}")
            result.error = f"API error: {e}"
        
        except Exception as e:
            logger.error(f"  ✗ Unexpected error: {e}")
            result.error = f"Unexpected error: {e}"
        
        return result
    
    def generate_summary(self, results: List[MRResult]) -> MRSummary:
        """
        Generate summary statistics from MR results.
        
        Args:
            results: List of MRResult objects
        
        Returns:
            MRSummary with aggregated statistics
        """
        # Collect statistics
        all_authors = set()
        mrs_by_project = {}
        mrs_by_author = defaultdict(int)
        
        projects_with_mrs = 0
        projects_with_errors = 0
        total_mrs = 0
        
        # Get filter info from first result
        target_branch = results[0].target_branch if results else None
        source_branch = results[0].source_branch if results else None
        state_filter = results[0].state_filter if results else "merged"
        
        for result in results:
            if result.has_mrs:
                projects_with_mrs += 1
            if result.error:
                projects_with_errors += 1
            
            total_mrs += result.total_mrs
            mrs_by_project[result.project_path] = result.total_mrs
            
            for mr in result.merge_requests:
                all_authors.add(mr.author_name)
                mrs_by_author[mr.author_name] += 1
        
        # Sort projects by MR count
        top_projects = sorted(
            mrs_by_project.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return MRSummary(
            target_branch=target_branch,
            source_branch=source_branch,
            state_filter=state_filter,
            date_range_start=None,  # Set by caller if needed
            date_range_end=None,
            total_projects=len(results),
            projects_with_mrs=projects_with_mrs,
            projects_with_errors=projects_with_errors,
            total_mrs=total_mrs,
            unique_authors=sorted(list(all_authors)),
            mrs_by_project=mrs_by_project,
            mrs_by_author=dict(mrs_by_author),
            top_projects=top_projects
        )





