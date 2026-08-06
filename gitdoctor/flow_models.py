"""
Data models for flow validation (branch route, containment, release reconciliation).

Separate from delta models — do not import DeltaCommit/DeltaResult here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlowPolicy:
    """Branch-flow policy for a project or preset."""
    premaster_prefix: str = "premaster"
    feature_prefixes: List[str] = field(default_factory=lambda: ["feature/"])
    allowed_master_sources: List[str] = field(default_factory=lambda: ["premaster"])
    allowed_premaster_sources: List[str] = field(default_factory=lambda: ["feature/"])
    exception_labels: List[str] = field(default_factory=lambda: ["flow-exception"])
    require_jira_in_commits: bool = True
    patch_search_limit: int = 200


@dataclass
class SourceCommitInfo:
    source_commit_sha: str
    short_id: str
    title: str
    jira_tickets: List[str] = field(default_factory=list)


@dataclass
class TraceabilityResult:
    status: str  # expanded | no_mr_link | access_denied | partial
    mr_iid: Optional[int] = None
    mr_web_url: Optional[str] = None
    source_commits: List[SourceCommitInfo] = field(default_factory=list)
    source_jira_tickets: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class MRFlowAssessment:
    """Per-MR route and containment assessment."""
    project_path: str
    project_id: int
    mr_iid: int
    title: str
    web_url: str
    source_branch: str
    target_branch: str
    merged_at: Optional[str]
    merged_by_username: Optional[str]
    merge_commit_sha: Optional[str]
    jira_tickets: List[str] = field(default_factory=list)
    route_status: str = ""  # COMPLIANT | VIOLATION_DIRECT_FEATURE | VIOLATION_OTHER | EXCEPTION
    containment_status: str = ""  # CONTAINED | MISSING_ON_PREMASTER | SKIPPED | NOT_CHECKED
    verified_by: str = ""  # sha | mr_trail | patch | none
    evidence: str = ""
    exception_id: Optional[str] = None
    backfill_required: bool = False


@dataclass
class ProjectFlowReport:
    project_id: int
    project_path: str
    premaster_ref: str
    target_ref: str
    assessments: List[MRFlowAssessment] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class FlowReportSummary:
    total_projects: int = 0
    total_mrs: int = 0
    compliant: int = 0
    violations: int = 0
    exceptions: int = 0
    missing_on_premaster: int = 0


@dataclass
class TicketReconciliation:
    jira_ticket: str
    status: str  # OK_BOTH | OK_PREMASTER_ONLY | MISSING_BOTH | MASTER_ONLY | NO_JIRA_IN_COMMITS
    projects: List[str] = field(default_factory=list)
    master_commits: List[str] = field(default_factory=list)
    premaster_commits: List[str] = field(default_factory=list)
    master_mrs: List[int] = field(default_factory=list)
    premaster_mrs: List[int] = field(default_factory=list)
    notes: str = ""


@dataclass
class ReleaseCheckReport:
    scope_label: str
    ticket_results: List[TicketReconciliation] = field(default_factory=list)
    flow_reports: List[ProjectFlowReport] = field(default_factory=list)
    open_exceptions: List[Dict] = field(default_factory=list)


@dataclass
class FlowValidationPreset:
    name: str
    projects: List[str] = field(default_factory=list)
    default_base_ref: Optional[str] = None
    default_target_ref: str = "master"
    premaster_ref: Optional[str] = None
    policy: FlowPolicy = field(default_factory=FlowPolicy)
