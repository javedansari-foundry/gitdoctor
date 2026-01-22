"""
Data models for GitDoctor.

Contains dataclasses for representing delta comparison results and merge request tracking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict


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


# ============================================================
# Merge Request Models
# ============================================================

@dataclass
class MergeRequest:
    """
    Represents a single merge request from GitLab.
    """
    mr_id: int              # Internal MR ID
    mr_iid: int             # Visible MR number (e.g., !123)
    title: str
    description: str
    state: str              # 'merged', 'opened', 'closed'
    source_branch: str
    target_branch: str
    author_name: str
    author_username: str
    merged_by_name: Optional[str] = None
    merged_by_username: Optional[str] = None
    merged_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    web_url: str = ""
    merge_commit_sha: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    
    @classmethod
    def from_api_response(cls, data: Dict) -> "MergeRequest":
        """Create MergeRequest from GitLab API response."""
        author = data.get("author", {}) or {}
        merged_by = data.get("merged_by", {}) or {}
        
        return cls(
            mr_id=data.get("id", 0),
            mr_iid=data.get("iid", 0),
            title=data.get("title", ""),
            description=data.get("description", "") or "",
            state=data.get("state", ""),
            source_branch=data.get("source_branch", ""),
            target_branch=data.get("target_branch", ""),
            author_name=author.get("name", "Unknown"),
            author_username=author.get("username", "unknown"),
            merged_by_name=merged_by.get("name") if merged_by else None,
            merged_by_username=merged_by.get("username") if merged_by else None,
            merged_at=data.get("merged_at"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            web_url=data.get("web_url", ""),
            merge_commit_sha=data.get("merge_commit_sha"),
            labels=data.get("labels", []) or []
        )


@dataclass
class MRResult:
    """
    Result of fetching merge requests for a single project.
    """
    # Project information
    project_id: int
    project_name: str
    project_path: str
    project_web_url: str
    
    # Filter information
    target_branch: Optional[str] = None
    source_branch: Optional[str] = None
    state_filter: str = "merged"
    
    # Results
    merge_requests: List[MergeRequest] = field(default_factory=list)
    total_mrs: int = 0
    
    # Status
    error: Optional[str] = None
    
    @property
    def has_mrs(self) -> bool:
        """Whether any merge requests were found."""
        return len(self.merge_requests) > 0
    
    @property
    def is_successful(self) -> bool:
        """Whether the fetch completed successfully."""
        return self.error is None
    
    def get_unique_authors(self) -> List[str]:
        """Get list of unique author names."""
        return sorted(list(set(mr.author_name for mr in self.merge_requests)))
    
    def get_mrs_by_author(self, author_name: str) -> List[MergeRequest]:
        """Get all MRs by a specific author."""
        return [mr for mr in self.merge_requests if mr.author_name == author_name]


@dataclass
class MRSummary:
    """
    Summary statistics for merge request tracking across multiple projects.
    """
    # Filter info
    target_branch: Optional[str]
    source_branch: Optional[str]
    state_filter: str
    date_range_start: Optional[str]
    date_range_end: Optional[str]
    
    # Statistics
    total_projects: int
    projects_with_mrs: int
    projects_with_errors: int
    total_mrs: int
    unique_authors: List[str] = field(default_factory=list)
    
    # Breakdown
    mrs_by_project: Dict[str, int] = field(default_factory=dict)
    mrs_by_author: Dict[str, int] = field(default_factory=dict)
    top_projects: List[tuple] = field(default_factory=list)  # [(project_path, count), ...]
    
    def __str__(self) -> str:
        """Format summary as human-readable string."""
        lines = [
            "=" * 60,
            "Merge Request Summary",
            "=" * 60,
        ]
        
        if self.target_branch:
            lines.append(f"Target Branch:           {self.target_branch}")
        if self.source_branch:
            lines.append(f"Source Branch:           {self.source_branch}")
        lines.append(f"State Filter:            {self.state_filter}")
        
        if self.date_range_start:
            lines.append(f"From Date:               {self.date_range_start}")
        if self.date_range_end:
            lines.append(f"To Date:                 {self.date_range_end}")
        
        lines.extend([
            "",
            f"Projects Searched:       {self.total_projects}",
            f"Projects with MRs:       {self.projects_with_mrs}",
            f"Projects with Errors:    {self.projects_with_errors}",
            "",
            f"Total Merge Requests:    {self.total_mrs}",
            f"Unique Authors:          {len(self.unique_authors)}",
        ])
        
        if self.top_projects:
            lines.append("")
            lines.append(f"Top {min(5, len(self.top_projects))} Projects by MR Count:")
            for i, (project_path, count) in enumerate(self.top_projects[:5], 1):
                lines.append(f"  {i}. {project_path}: {count} MRs")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


# ============================================================
# MR Changes Models (for test selection)
# ============================================================

@dataclass
class FileChange:
    """
    Represents a single file change in a commit or MR.
    """
    old_path: str
    new_path: str
    diff: str = ""
    new_file: bool = False
    deleted_file: bool = False
    renamed_file: bool = False
    a_mode: Optional[str] = None
    b_mode: Optional[str] = None
    
    @property
    def file_extension(self) -> str:
        """Get file extension (e.g., '.py', '.java')."""
        if self.new_path:
            parts = self.new_path.rsplit('.', 1)
            return f".{parts[1]}" if len(parts) > 1 else ""
        return ""
    
    @property
    def is_test_file(self) -> bool:
        """Heuristic to detect if this is a test file."""
        path_lower = self.new_path.lower()
        return any([
            'test' in path_lower,
            'spec' in path_lower,
            path_lower.endswith('_test.py'),
            path_lower.endswith('_test.java'),
            path_lower.endswith('.spec.ts'),
            path_lower.endswith('.spec.js'),
            '/tests/' in path_lower,
            '/test/' in path_lower,
        ])


@dataclass
class CommitChange:
    """
    Represents a commit with its file changes.
    """
    commit_sha: str
    short_id: str
    title: str
    message: str
    author_name: str
    author_email: str
    created_at: str
    web_url: str
    file_changes: List[FileChange] = field(default_factory=list)
    jira_tickets: List[str] = field(default_factory=list)
    
    @property
    def total_files_changed(self) -> int:
        """Total number of files changed in this commit."""
        return len(self.file_changes)
    
    @property
    def files_added(self) -> int:
        """Number of new files."""
        return sum(1 for f in self.file_changes if f.new_file)
    
    @property
    def files_deleted(self) -> int:
        """Number of deleted files."""
        return sum(1 for f in self.file_changes if f.deleted_file)
    
    @property
    def files_modified(self) -> int:
        """Number of modified files."""
        return sum(1 for f in self.file_changes if not f.new_file and not f.deleted_file)


@dataclass
class MRChangesResult:
    """
    Complete changeset for a merge request - all data needed for test selection.
    """
    # MR metadata
    project_id: int
    project_name: str
    project_path: str
    project_web_url: str
    mr_iid: int
    mr_id: int
    title: str
    description: str
    state: str
    source_branch: str
    target_branch: str
    author_name: str
    author_username: str
    merged_by_name: Optional[str] = None
    merged_at: Optional[str] = None
    created_at: str = ""
    web_url: str = ""
    merge_commit_sha: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    
    # Changes data
    commits: List[CommitChange] = field(default_factory=list)
    all_file_changes: List[FileChange] = field(default_factory=list)
    jira_tickets: List[str] = field(default_factory=list)
    
    # Status
    error: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Whether the fetch completed successfully."""
        return self.error is None
    
    @property
    def total_commits(self) -> int:
        """Total number of commits in this MR."""
        return len(self.commits)
    
    @property
    def total_files_changed(self) -> int:
        """Total unique files changed across all commits."""
        unique_files = set()
        for fc in self.all_file_changes:
            unique_files.add(fc.new_path if fc.new_path else fc.old_path)
        return len(unique_files)
    
    @property
    def files_by_extension(self) -> Dict[str, int]:
        """Group files by extension."""
        extensions: Dict[str, int] = {}
        for fc in self.all_file_changes:
            ext = fc.file_extension or 'no_extension'
            extensions[ext] = extensions.get(ext, 0) + 1
        return extensions
    
    @property
    def changed_directories(self) -> List[str]:
        """Get list of unique directories that have changes."""
        dirs = set()
        for fc in self.all_file_changes:
            path = fc.new_path if fc.new_path else fc.old_path
            if '/' in path:
                directory = '/'.join(path.split('/')[:-1])
                dirs.add(directory)
        return sorted(list(dirs))
    
    @property
    def unique_jira_tickets(self) -> List[str]:
        """Get deduplicated list of JIRA tickets."""
        return sorted(list(set(self.jira_tickets)))
    
    def get_files_by_pattern(self, pattern: str) -> List[FileChange]:
        """
        Get files matching a pattern (useful for test selection).
        
        Args:
            pattern: Pattern to match (e.g., 'services/', '.java', 'controller')
        
        Returns:
            List of FileChange objects matching the pattern
        """
        return [
            fc for fc in self.all_file_changes 
            if pattern.lower() in fc.new_path.lower()
        ]
    
    def get_non_test_files(self) -> List[FileChange]:
        """Get all non-test files (actual source code changes)."""
        return [fc for fc in self.all_file_changes if not fc.is_test_file]
    
    def get_test_files(self) -> List[FileChange]:
        """Get all test files."""
        return [fc for fc in self.all_file_changes if fc.is_test_file]

