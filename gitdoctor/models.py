"""
Data models for GitDoctor.

Contains dataclasses for representing delta comparison results.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DeltaCommit:
    """
    Represents a single commit in a delta comparison.
    
    This captures all relevant information about a commit that exists
    in the target reference but not in the base reference.
    """
    commit_sha: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    authored_date: str
    committed_date: str
    committer_name: str
    committer_email: str
    web_url: str
    parent_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Normalize empty strings to empty list for parent_ids."""
        if isinstance(self.parent_ids, str):
            self.parent_ids = []


@dataclass
class DeltaResult:
    """
    Result of comparing two references (tags/branches/commits) in a single project.
    
    Contains all commits between base_ref and target_ref, along with
    metadata about the comparison.
    """
    # Project information
    project_id: int
    project_name: str
    project_path: str
    project_web_url: str
    
    # Reference information
    base_ref: str
    target_ref: str
    base_exists: bool = False
    target_exists: bool = False
    
    # Comparison results
    commits: List[DeltaCommit] = field(default_factory=list)
    total_commits: int = 0  # Total commits in delta (before date filtering)
    
    # Commit counts from each ref (for transparency)
    base_commit_count: int = 0   # Total commits in base ref
    target_commit_count: int = 0  # Total commits in target ref
    
    # Statistics
    total_additions: int = 0
    total_deletions: int = 0
    files_changed: int = 0
    
    # Status
    compare_timeout: bool = False
    compare_same_ref: bool = False
    error: Optional[str] = None
    
    @property
    def has_changes(self) -> bool:
        """Whether there are any commits in the delta."""
        return len(self.commits) > 0
    
    @property
    def is_successful(self) -> bool:
        """Whether the comparison completed successfully."""
        return self.error is None and self.base_exists and self.target_exists
    
    def get_unique_authors(self) -> List[str]:
        """Get list of unique author names."""
        authors = set()
        for commit in self.commits:
            authors.add(commit.author_name)
        return sorted(list(authors))
    
    def get_commits_by_author(self, author_name: str) -> List[DeltaCommit]:
        """Get all commits by a specific author."""
        return [c for c in self.commits if c.author_name == author_name]


@dataclass
class DeltaSummary:
    """
    Summary statistics for a delta comparison across multiple projects.
    """
    base_ref: str
    target_ref: str
    total_projects: int
    projects_with_changes: int
    projects_without_changes: int
    projects_with_errors: int
    total_commits: int
    total_files_changed: int
    total_additions: int
    total_deletions: int
    unique_authors: List[str] = field(default_factory=list)
    
    # Commit counts from refs (for transparency)
    total_base_commits: int = 0   # Total commits across all base refs
    total_target_commits: int = 0  # Total commits across all target refs
    
    # Top projects by commit count
    top_projects: List[tuple] = field(default_factory=list)  # [(project_path, commit_count), ...]
    
    def __str__(self) -> str:
        """Format summary as human-readable string."""
        lines = [
            "=" * 60,
            "Delta Discovery Summary",
            "=" * 60,
            f"Base Reference:          {self.base_ref}",
            f"Target Reference:        {self.target_ref}",
            f"Projects Searched:       {self.total_projects}",
            f"Projects with Changes:   {self.projects_with_changes}",
            f"Projects without Changes: {self.projects_without_changes}",
            f"Projects with Errors:    {self.projects_with_errors}",
            "",
            f"Commits in Base Ref:     {self.total_base_commits}",
            f"Commits in Target Ref:   {self.total_target_commits}",
            f"Delta (Unique to Target): {self.total_commits}",
            f"Total Files Changed:     {self.total_files_changed}",
        ]
        
        if self.total_additions or self.total_deletions:
            lines.extend([
                f"Total Additions:         +{self.total_additions}",
                f"Total Deletions:         -{self.total_deletions}",
            ])
        
        if self.unique_authors:
            lines.append(f"Unique Authors:          {len(self.unique_authors)}")
        
        if self.top_projects:
            lines.append("")
            lines.append(f"Top {min(5, len(self.top_projects))} Projects by Commit Count:")
            for i, (project_path, count) in enumerate(self.top_projects[:5], 1):
                lines.append(f"  {i}. {project_path}: {count} commits")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)

