"""
Branch flow validation: route rules and premaster containment.
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Dict, List, Optional, Set

from .api_client import GitLabClient
from .flow_models import FlowPolicy, FlowReportSummary, MRFlowAssessment, ProjectFlowReport
from .flow_policy import classify_mr_route
from .flow_scope import FlowCommitIndexer
from .jira_integration import JIRALinker
from .models import MergeRequest
from .mr_finder import MRFinder
from .project_resolver import ProjectInfo
from .traceability import CommitTraceabilityBuilder, extract_jira_tickets


logger = logging.getLogger(__name__)

EXCEPTION_BLOCK = re.compile(
    r"##\s*Flow exception\s*\n"
    r".*?Ticket:\s*([A-Z][A-Z0-9]+-\d+)",
    re.IGNORECASE | re.DOTALL,
)


def extract_jira_from_mr(mr: MergeRequest, linker: Optional[JIRALinker]) -> List[str]:
    tickets = set()
    for text in (mr.title, mr.description):
        if linker:
            tickets.update(linker.extract_tickets_from_text(text or ""))
        else:
            tickets.update(extract_jira_tickets(text or ""))
    return sorted(tickets)


def parse_exception_ticket(description: str) -> Optional[str]:
    if not description:
        return None
    match = EXCEPTION_BLOCK.search(description)
    if match:
        return match.group(1).upper()
    return None


def diff_fingerprint(diff_entries: List[dict]) -> str:
    parts = []
    for entry in sorted(diff_entries, key=lambda e: e.get("new_path", "")):
        path = entry.get("new_path") or entry.get("old_path", "")
        diff_text = entry.get("diff", "") or ""
        parts.append(f"{path}\n{diff_text}")
    raw = "\n---\n".join(parts)
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


class BranchFlowValidator:
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
        self.mr_finder = MRFinder(client, projects)
        self.indexer = FlowCommitIndexer(client)
        self.trace_builder = CommitTraceabilityBuilder(client)

    def run_flow_report(
        self,
        premaster_ref: str,
        target_branch: str = "master",
        merged_after: Optional[str] = None,
        merged_before: Optional[str] = None,
        source_branch_prefix: Optional[str] = None,
        check_containment: bool = True,
    ) -> List[ProjectFlowReport]:
        mr_results = self.mr_finder.find_merge_requests(
            target_branch=target_branch,
            source_branch=None,
            state="merged",
            merged_after=merged_after,
            merged_before=merged_before,
        )
        reports: List[ProjectFlowReport] = []
        premaster_sets: Dict[int, Set[str]] = {}

        for mr_result in mr_results:
            report = ProjectFlowReport(
                project_id=mr_result.project_id,
                project_path=mr_result.project_path,
                premaster_ref=premaster_ref,
                target_ref=target_branch,
            )
            if mr_result.error:
                report.error = mr_result.error
                reports.append(report)
                continue

            premaster_shas = premaster_sets.get(mr_result.project_id)
            if premaster_shas is None and check_containment:
                try:
                    premaster_shas = self.indexer.build_premaster_sha_set(
                        mr_result.project_id, premaster_ref
                    )
                    premaster_sets[mr_result.project_id] = premaster_shas
                except Exception as e:
                    logger.warning(f"Could not index premaster for {mr_result.project_path}: {e}")
                    premaster_shas = set()

            for mr in mr_result.merge_requests:
                if source_branch_prefix and not (
                    mr.source_branch or ""
                ).startswith(source_branch_prefix):
                    continue

                assessment = self._assess_mr(
                    project_id=mr_result.project_id,
                    project_path=mr_result.project_path,
                    mr=mr,
                    premaster_ref=premaster_ref,
                    premaster_shas=premaster_shas or set(),
                    check_containment=check_containment,
                )
                report.assessments.append(assessment)

            reports.append(report)
        return reports

    def _assess_mr(
        self,
        project_id: int,
        project_path: str,
        mr: MergeRequest,
        premaster_ref: str,
        premaster_shas: Set[str],
        check_containment: bool,
    ) -> MRFlowAssessment:
        route = classify_mr_route(mr, self.policy, target="master")
        tickets = extract_jira_from_mr(mr, self.jira_linker)

        assessment = MRFlowAssessment(
            project_path=project_path,
            project_id=project_id,
            mr_iid=mr.mr_iid,
            title=mr.title,
            web_url=mr.web_url,
            source_branch=mr.source_branch,
            target_branch=mr.target_branch,
            merged_at=mr.merged_at,
            merged_by_username=mr.merged_by_username,
            merge_commit_sha=mr.merge_commit_sha,
            jira_tickets=tickets,
            route_status=route,
            backfill_required=route in ("VIOLATION_DIRECT_FEATURE", "EXCEPTION"),
        )

        if route == "EXCEPTION":
            ex_ticket = parse_exception_ticket(mr.description)
            if ex_ticket and ex_ticket not in tickets:
                assessment.jira_tickets = sorted(set(tickets + [ex_ticket]))

        if not check_containment or mr.target_branch != "master":
            assessment.containment_status = "NOT_CHECKED"
            return assessment

        if route == "EXCEPTION" and not check_containment:
            assessment.containment_status = "SKIPPED"
            return assessment

        contained, verified_by, evidence = self._check_containment(
            project_id, project_path, mr, premaster_ref, premaster_shas
        )
        assessment.containment_status = "CONTAINED" if contained else "MISSING_ON_PREMASTER"
        assessment.verified_by = verified_by
        assessment.evidence = evidence
        return assessment

    def _check_containment(
        self,
        project_id: int,
        project_path: str,
        mr: MergeRequest,
        premaster_ref: str,
        premaster_shas: Set[str],
    ) -> tuple:
        try:
            mr_commits = self.client.get_merge_request_commits(project_id, mr.mr_iid)
        except Exception:
            return False, "none", ""

        for commit in mr_commits:
            sha = commit.get("id", "")
            if not sha:
                continue
            if sha in premaster_shas:
                return True, "sha", sha
            refs = self.client.list_commit_refs(project_id, sha, ref_type="branch")
            ref_names = [r.get("name", "") for r in refs]
            if premaster_ref in ref_names or any(
                n.startswith(self.policy.premaster_prefix) for n in ref_names
            ):
                return True, "sha", sha

        merge_sha = mr.merge_commit_sha
        if merge_sha and merge_sha in premaster_shas:
            return True, "sha", merge_sha

        if merge_sha:
            from .project_resolver import ProjectInfo

            project = ProjectInfo(
                id=project_id,
                name=project_path.split("/")[-1] if project_path else "",
                path_with_namespace=project_path,
                web_url="",
            )
            trace = self.trace_builder.build_for_commit(
                project,
                merge_sha,
                commit_message="",
                commit_title=mr.title,
            )
            for sc in trace.source_commits:
                if sc.source_commit_sha in premaster_shas:
                    return True, "mr_trail", sc.source_commit_sha

        if mr_commits and premaster_shas:
            try:
                fp = diff_fingerprint(
                    self.client.get_commit_diff(project_id, mr_commits[0].get("id", ""))
                )
                checked = 0
                for pm_sha in list(premaster_shas)[: self.policy.patch_search_limit]:
                    checked += 1
                    try:
                        pm_fp = diff_fingerprint(
                            self.client.get_commit_diff(project_id, pm_sha)
                        )
                        if pm_fp == fp:
                            return True, "patch", pm_sha
                    except Exception:
                        continue
            except Exception:
                pass

        return False, "none", ""

    def summarize(self, reports: List[ProjectFlowReport]) -> FlowReportSummary:
        summary = FlowReportSummary(total_projects=len(reports))
        for report in reports:
            for a in report.assessments:
                summary.total_mrs += 1
                if a.route_status == "COMPLIANT":
                    summary.compliant += 1
                elif a.route_status == "EXCEPTION":
                    summary.exceptions += 1
                elif a.route_status.startswith("VIOLATION"):
                    summary.violations += 1
                if a.containment_status == "MISSING_ON_PREMASTER":
                    summary.missing_on_premaster += 1
        return summary
