"""
Release reconciliation: Jira scope vs git evidence on premaster and master.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from .api_client import GitLabClient
from .branch_flow_validator import BranchFlowValidator
from .flow_models import FlowPolicy, ReleaseCheckReport, TicketReconciliation
from .flow_scope import FlowCommitIndexer
from .jira_integration import JIRALinker
from .mr_finder import MRFinder
from .project_resolver import ProjectInfo
from .traceability import extract_jira_tickets


logger = logging.getLogger(__name__)


def _jira_from_mr(title: str, description: str, linker: Optional[JIRALinker]) -> Set[str]:
    tickets: Set[str] = set()
    for text in (title, description):
        if linker:
            tickets.update(linker.extract_tickets_from_text(text or ""))
        else:
            tickets.update(extract_jira_tickets(text or ""))
    return tickets


class ReleaseReconciler:
    def __init__(
        self,
        client: GitLabClient,
        projects: List[ProjectInfo],
        policy: Optional[FlowPolicy] = None,
        jira_linker: Optional[JIRALinker] = None,
    ):
        self.client = client
        self.projects = projects
        self.policy = policy or FlowPolicy()
        self.jira_linker = jira_linker
        self.indexer = FlowCommitIndexer(client)
        self.mr_finder = MRFinder(client, projects)

    def reconcile(
        self,
        ticket_keys: List[str],
        base_ref: str,
        target_ref: str,
        premaster_ref: str,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        merged_after: Optional[str] = None,
        merged_before: Optional[str] = None,
        scope_label: str = "release",
        include_flow_report: bool = True,
    ) -> ReleaseCheckReport:
        report = ReleaseCheckReport(scope_label=scope_label)
        ticket_set = set(ticket_keys)

        master_jira: Dict[str, Set[str]] = {k: set() for k in ticket_keys}
        premaster_jira: Dict[str, Set[str]] = {k: set() for k in ticket_keys}
        master_mrs: Dict[str, Set[int]] = {k: set() for k in ticket_keys}
        premaster_mrs: Dict[str, Set[int]] = {k: set() for k in ticket_keys}
        ticket_projects: Dict[str, Set[str]] = {k: set() for k in ticket_keys}

        for project in self.projects:
            idx_master = self.indexer.index_project(
                project, base_ref, target_ref, after_date=after_date, before_date=before_date
            )
            for commit in idx_master.commits:
                for t in commit.jira_tickets:
                    if t in ticket_set:
                        master_jira[t].add(commit.sha)
                        ticket_projects[t].add(project.path_with_namespace)

            idx_pm = self.indexer.index_project(
                project, base_ref, premaster_ref, after_date=after_date, before_date=before_date
            )
            for commit in idx_pm.commits:
                for t in commit.jira_tickets:
                    if t in ticket_set:
                        premaster_jira[t].add(commit.sha)
                        ticket_projects[t].add(project.path_with_namespace)

        self._index_mrs(
            ticket_set, ticket_projects, master_jira, master_mrs,
            "master", merged_after, merged_before,
        )
        self._index_mrs(
            ticket_set, ticket_projects, premaster_jira, premaster_mrs,
            premaster_ref, merged_after, merged_before,
        )

        for key in ticket_keys:
            on_master = bool(master_jira.get(key) or master_mrs.get(key))
            on_pm = bool(premaster_jira.get(key) or premaster_mrs.get(key))
            if on_master and on_pm:
                status = "OK_BOTH"
            elif on_pm:
                status = "OK_PREMASTER_ONLY"
            elif on_master:
                status = "MASTER_ONLY"
            else:
                status = "MISSING_BOTH"

            report.ticket_results.append(
                TicketReconciliation(
                    jira_ticket=key,
                    status=status,
                    projects=sorted(ticket_projects.get(key, set())),
                    master_commits=sorted(master_jira.get(key, set())),
                    premaster_commits=sorted(premaster_jira.get(key, set())),
                    master_mrs=sorted(master_mrs.get(key, set())),
                    premaster_mrs=sorted(premaster_mrs.get(key, set())),
                )
            )

        if include_flow_report:
            validator = BranchFlowValidator(
                self.client, self.projects, self.policy, self.jira_linker
            )
            report.flow_reports = validator.run_flow_report(
                premaster_ref=premaster_ref,
                target_branch="master",
                merged_after=merged_after,
                merged_before=merged_before,
            )

        return report

    def _index_mrs(
        self,
        ticket_set: Set[str],
        ticket_projects: Dict[str, Set[str]],
        _commits: Dict[str, Set[str]],
        jira_mrs: Dict[str, Set[int]],
        target_branch: str,
        merged_after: Optional[str],
        merged_before: Optional[str],
    ) -> None:
        results = self.mr_finder.find_merge_requests(
            target_branch=target_branch,
            state="merged",
            merged_after=merged_after,
            merged_before=merged_before,
        )
        for mr_result in results:
            for mr in mr_result.merge_requests:
                for t in _jira_from_mr(mr.title, mr.description, self.jira_linker):
                    if t in ticket_set:
                        jira_mrs.setdefault(t, set()).add(mr.mr_iid)
                        ticket_projects.setdefault(t, set()).add(mr_result.project_path)
