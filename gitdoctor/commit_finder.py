"""
Commit finder module.

Searches for commits across GitLab projects and collects metadata.
"""

from dataclasses import dataclass
from typing import List, Iterable, Optional
import logging

from .api_client import GitLabClient, GitLabNotFound, GitLabAPIError
from .project_resolver import ProjectInfo


logger = logging.getLogger(__name__)


@dataclass
class CommitSearchResult:
    """Result of searching for a commit in a project."""
    commit_sha: str
    project_id: int
    project_name: str
    project_path: str
    project_web_url: str
    commit_web_url: str = ""
    author_name: str = ""
    author_email: str = ""
    title: str = ""
    created_at: str = ""
    branches: str = ""  # Pipe-separated list of branch names
    tags: str = ""  # Pipe-separated list of tag names
    found: bool = False
    error: str = ""


class CommitFinder:
    """
    Searches for commits across multiple GitLab projects.
    
    For each commit found, collects detailed metadata including:
    - Commit details (author, title, date)
    - All branches that contain the commit
    - All tags that contain the commit
    """

    def __init__(self, client: GitLabClient, projects: List[ProjectInfo]):
        """
        Initialize commit finder.

        Args:
            client: GitLab API client
            projects: List of projects to search
        """
        self.client = client
        self.projects = projects

    def search_commits(self, commit_shas: Iterable[str]) -> List[CommitSearchResult]:
        """
        Search for commits across all configured projects.

        Args:
            commit_shas: Iterable of commit SHAs to search for

        Returns:
            List of CommitSearchResult objects. One result per (commit, project) pair.
            If a commit is not found in any project, no results are returned for it.
        """
        results = []
        commit_list = list(commit_shas)
        
        logger.info(
            f"Searching for {len(commit_list)} commits across {len(self.projects)} projects"
        )
        
        for i, commit_sha in enumerate(commit_list, 1):
            commit_sha = commit_sha.strip()
            if not commit_sha:
                continue
            
            logger.info(f"[{i}/{len(commit_list)}] Searching for commit {commit_sha}")
            commit_results = self._search_commit_in_projects(commit_sha)
            results.extend(commit_results)
            
            if commit_results:
                logger.info(
                    f"  Found in {len(commit_results)} project(s)"
                )
            else:
                logger.warning(f"  Commit {commit_sha} not found in any project")
        
        logger.info(f"Search complete. Found {len(results)} commit-project matches.")
        return results

    def _search_commit_in_projects(self, commit_sha: str) -> List[CommitSearchResult]:
        """
        Search for a single commit across all projects.

        Args:
            commit_sha: Commit SHA to search for

        Returns:
            List of CommitSearchResult objects for projects where commit was found
        """
        results = []
        
        for project in self.projects:
            result = self._search_commit_in_project(commit_sha, project)
            if result.found or result.error:
                results.append(result)
        
        return results

    def _search_commit_in_project(
        self,
        commit_sha: str,
        project: ProjectInfo
    ) -> CommitSearchResult:
        """
        Search for a commit in a specific project.

        Args:
            commit_sha: Commit SHA to search for
            project: Project to search in

        Returns:
            CommitSearchResult with found=True if commit exists, otherwise found=False
        """
        result = CommitSearchResult(
            commit_sha=commit_sha,
            project_id=project.id,
            project_name=project.name,
            project_path=project.path_with_namespace,
            project_web_url=project.web_url,
        )

        try:
            # Fetch commit details
            commit_data = self.client.get_commit(project.id, commit_sha)
            
            # Populate commit metadata
            result.found = True
            
            # Get web_url from API, or construct it manually
            # Normalize: always use clean URLs without '/-/' segment
            api_web_url = commit_data.get("web_url", "") or ""
            
            # Normalize: remove '/-/' segment if present
            if "/-/commit/" in api_web_url:
                normalized_web_url = api_web_url.replace("/-/commit/", "/commit/")
            else:
                normalized_web_url = api_web_url
            
            # If still empty, build manually from project.web_url
            if not normalized_web_url:
                base = project.web_url.rstrip("/")
                # Normalized format: <project.web_url>/commit/<sha> (no '/-/')
                normalized_web_url = f"{base}/commit/{commit_sha}"
            
            result.commit_web_url = normalized_web_url
            
            result.author_name = commit_data.get("author_name", "")
            result.author_email = commit_data.get("author_email", "")
            result.title = commit_data.get("title", "")
            result.created_at = commit_data.get("created_at", "")
            
            # Fetch branches and tags that contain this commit
            try:
                refs = self.client.list_commit_refs(project.id, commit_sha)
                branches = []
                tags = []
                
                for ref in refs:
                    ref_type = ref.get("type", "")
                    ref_name = ref.get("name", "")
                    
                    if ref_type == "branch":
                        branches.append(ref_name)
                    elif ref_type == "tag":
                        tags.append(ref_name)
                
                result.branches = "|".join(branches) if branches else ""
                result.tags = "|".join(tags) if tags else ""
                
            except GitLabAPIError as e:
                # If we can't fetch refs, still return the commit info
                logger.warning(
                    f"Failed to fetch refs for commit {commit_sha} "
                    f"in project {project.path_with_namespace}: {e}"
                )
                result.error = f"Could not fetch refs: {str(e)}"

        except GitLabNotFound:
            # Commit not found in this project - this is expected and normal
            result.found = False
            return result
        except GitLabAPIError as e:
            # Other API errors
            result.found = False
            result.error = str(e)
            logger.error(
                f"Error searching for commit {commit_sha} "
                f"in project {project.path_with_namespace}: {e}"
            )

        return result


def load_commit_shas_from_file(file_path: str) -> List[str]:
    """
    Load commit SHAs from a text file.

    Args:
        file_path: Path to file containing commit SHAs (one per line)

    Returns:
        List of commit SHAs (stripped of whitespace, empty lines removed)

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    try:
        with open(file_path, 'r') as f:
            commits = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(commits)} commit SHAs from {file_path}")
        return commits
    except FileNotFoundError:
        raise FileNotFoundError(f"Commits file not found: {file_path}")
    except Exception as e:
        raise IOError(f"Failed to read commits file {file_path}: {e}")

