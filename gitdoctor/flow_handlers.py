"""
CLI handlers for flow validation commands (separate from delta handlers).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

from .api_client import GitLabClient, GitLabAPIError
from .branch_flow_validator import BranchFlowValidator
from .flow_policy import classify_mr_route
from .cli_utils import filter_projects_by_cli_args, validate_date_range
from .config import load_config, ConfigError
from .exception_registry import ExceptionRegistry
from .flow_exporter import FlowCSVExporter, FlowHTMLExporter, FlowJSONExporter
from .flow_models import FlowPolicy
from .flow_scope import resolve_preset
from .jira_client import JiraClient, JiraClientError, resolve_release_ticket_keys
from .jira_integration import create_jira_linker
from .project_resolver import resolve_projects
from .release_reconciler import ReleaseReconciler


logger = logging.getLogger(__name__)


def _build_client(config) -> GitLabClient:
    return GitLabClient(
        base_url=config.gitlab.base_url,
        private_token=config.gitlab.private_token,
        api_version=config.gitlab.api_version,
        verify_ssl=config.gitlab.verify_ssl,
        timeout_seconds=config.gitlab.timeout_seconds,
    )


def _resolve_projects_and_policy(args, config):
    client = _build_client(config)
    projects = resolve_projects(client, config)
    projects = filter_projects_by_cli_args(
        projects, getattr(args, "projects", None), getattr(args, "project_ids", None)
    )

    policy = config.flow_validation.default_policy
    if getattr(args, "preset", None) and config.flow_validation.presets:
        preset = resolve_preset(config.flow_validation, args.preset)
        if preset.projects:
            path_set = set(preset.projects)
            projects = [p for p in projects if p.path_with_namespace in path_set]
        policy = preset.policy

    jira_linker = create_jira_linker(
        getattr(args, "jira_url", None) or config.jira.base_url,
        getattr(args, "jira_project", None) or config.jira.project_key,
    )
    return client, projects, policy, jira_linker


def _export_flow(reports, summary, output, fmt):
    if fmt == "csv":
        FlowCSVExporter().export_flow_report(reports, output)
    elif fmt == "json":
        FlowJSONExporter().export_flow_report(reports, summary, output)
    elif fmt == "html":
        FlowHTMLExporter().export_flow_report(reports, summary, output)


def handle_flow_report_command(args) -> None:
    try:
        config = load_config(args.config)
        client, projects, policy, jira_linker = _resolve_projects_and_policy(args, config)

        merged_after, merged_before = None, None
        if getattr(args, "after", None) or getattr(args, "before", None):
            merged_after, merged_before = validate_date_range(args.after, args.before)

        premaster = args.premaster
        if args.preset and config.flow_validation.presets:
            preset = resolve_preset(config.flow_validation, args.preset)
            premaster = premaster or preset.premaster_ref

        if not premaster:
            logger.error("--premaster is required (or set premaster_ref in preset)")
            sys.exit(1)

        validator = BranchFlowValidator(client, projects, policy, jira_linker)
        reports = validator.run_flow_report(
            premaster_ref=premaster,
            target_branch=args.target or "master",
            merged_after=merged_after,
            merged_before=merged_before,
            source_branch_prefix=getattr(args, "source_prefix", None),
            check_containment=not args.no_containment,
        )
        summary = validator.summarize(reports)
        print(summary.__dict__)
        _export_flow(reports, summary, args.output, args.format)
        logger.info(f"Flow report written to {args.output}")

        if summary.violations or summary.missing_on_premaster:
            sys.exit(2)
    except (ConfigError, ValueError, GitLabAPIError) as e:
        logger.error(str(e))
        sys.exit(1)


def handle_release_check_command(args) -> None:
    try:
        config = load_config(args.config)
        client, projects, policy, jira_linker = _resolve_projects_and_policy(args, config)

        jira_client = None
        if config.jira.email and config.jira.api_token and config.jira.base_url:
            jira_client = JiraClient(
                config.jira.base_url, config.jira.email, config.jira.api_token
            )

        jql = getattr(args, "jira_jql", None) or config.jira.default_jql
        tickets = resolve_release_ticket_keys(
            jira_csv=getattr(args, "jira_csv", None),
            jira_jql=jql,
            jira_client=jira_client if jql else None,
        )
        if not tickets:
            logger.error("No JIRA tickets in scope (provide --jira-csv or --jira-jql)")
            sys.exit(1)

        after_iso, before_iso = None, None
        if getattr(args, "after", None) or getattr(args, "before", None):
            after_iso, before_iso = validate_date_range(args.after, args.before)
        merged_after, merged_before = after_iso, before_iso

        premaster = args.premaster
        base_ref = args.base_ref
        target_ref = args.target_ref or "master"
        if args.preset:
            preset = resolve_preset(config.flow_validation, args.preset)
            premaster = premaster or preset.premaster_ref
            base_ref = base_ref or preset.default_base_ref
            target_ref = target_ref or preset.default_target_ref

        if not premaster or not base_ref:
            logger.error("--premaster and --base-ref are required")
            sys.exit(1)

        reconciler = ReleaseReconciler(client, projects, policy, jira_linker)
        report = reconciler.reconcile(
            ticket_keys=tickets,
            base_ref=base_ref,
            target_ref=target_ref,
            premaster_ref=premaster,
            after_date=after_iso,
            before_date=before_iso,
            merged_after=merged_after,
            merged_before=merged_before,
            scope_label=getattr(args, "scope_label", "release"),
            include_flow_report=not args.no_flow_report,
        )

        reg_path = config.flow_validation.exception_registry_path or "flow-exceptions"
        registry = ExceptionRegistry(reg_path)
        report.open_exceptions = [r.to_dict() for r in registry.list_open()]

        fmt = args.format
        if fmt == "csv":
            FlowCSVExporter().export_release_check(report, args.output)
        elif fmt == "json":
            FlowJSONExporter().export_release_check(report, args.output)
        else:
            FlowHTMLExporter().export_release_check(report, args.output)

        missing = sum(1 for t in report.ticket_results if t.status == "MISSING_BOTH")
        master_only = sum(1 for t in report.ticket_results if t.status == "MASTER_ONLY")
        logger.info(f"Tickets: {len(tickets)} | MISSING_BOTH: {missing} | MASTER_ONLY: {master_only}")
        if missing or master_only:
            sys.exit(2)
    except (ConfigError, ValueError, GitLabAPIError, JiraClientError) as e:
        logger.error(str(e))
        sys.exit(1)


def handle_validate_mr_command(args) -> None:
    try:
        config = load_config(args.config)
        client, projects, policy, jira_linker = _resolve_projects_and_policy(args, config)

        project_path = args.project
        project = None
        if str(args.project).isdigit():
            pid = int(args.project)
            for p in projects:
                if p.id == pid:
                    project = p
                    project_path = p.path_with_namespace
                    break
        else:
            for p in projects:
                if p.path_with_namespace == args.project:
                    project = p
                    break
        if not project:
            data = client.get_project_by_path(args.project)
            from .project_resolver import ProjectInfo
            project = ProjectInfo(
                id=data["id"],
                name=data["name"],
                path_with_namespace=data["path_with_namespace"],
                web_url=data.get("web_url", ""),
            )
            project_path = project.path_with_namespace

        mr_data = client.get_merge_request(project.id, args.mr_iid)
        from .models import MergeRequest
        mr = MergeRequest.from_api_response(mr_data)
        target = args.target or mr.target_branch

        from .flow_policy import classify_premaster_mr_route

        validator = BranchFlowValidator(client, [project], policy, jira_linker)
        premaster = args.premaster or "premaster"
        if target == "master":
            route = classify_mr_route(mr, policy, target="master")
        else:
            route = classify_premaster_mr_route(mr, policy)

        assessment = validator._assess_mr(
            project.id,
            project_path,
            mr,
            premaster,
            validator.indexer.build_premaster_sha_set(project.id, premaster),
            check_containment=(target == "master"),
        )
        assessment.route_status = route

        print(f"Route: {assessment.route_status}")
        print(f"Containment: {assessment.containment_status} ({assessment.verified_by})")
        print(f"JIRA: {', '.join(assessment.jira_tickets)}")

        ok = assessment.route_status in ("COMPLIANT", "EXCEPTION")
        if args.target == "master" and assessment.containment_status == "MISSING_ON_PREMASTER":
            ok = assessment.route_status == "EXCEPTION"
        sys.exit(0 if ok else 1)
    except (ConfigError, GitLabAPIError) as e:
        logger.error(str(e))
        sys.exit(1)


def handle_flow_exception_command(args) -> None:
    config = load_config(args.config)
    reg_path = args.registry_dir or config.flow_validation.exception_registry_path or "flow-exceptions"
    registry = ExceptionRegistry(reg_path)

    if args.exception_action == "register":
        rec = registry.register(
            project_path=args.project,
            mr_iid=args.mr_iid,
            jira_ticket=args.ticket,
            reason=args.reason,
            requested_by=getattr(args, "requested_by", "") or "",
            approved_by=getattr(args, "approved_by", "") or "",
            master_merge_commit=getattr(args, "merge_commit", None),
        )
        print(f"Registered {rec.exception_id} -> {registry._path_for(rec)}")
    elif args.exception_action == "list":
        for rec in registry.list_all():
            flag = "OPEN" if rec.backfill_required and not rec.backfilled else "CLOSED"
            print(f"{rec.exception_id} [{flag}] {rec.project_path} !{rec.mr_iid} {rec.jira_ticket}")
    elif args.exception_action == "close":
        rec = registry.close_backfill(args.exception_id, getattr(args, "backfill_mr", None))
        if rec:
            print(f"Closed {rec.exception_id}")
        else:
            logger.error("Exception not found")
            sys.exit(1)
