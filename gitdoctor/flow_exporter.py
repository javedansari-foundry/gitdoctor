"""Exporters for flow validation reports (separate from delta_exporter)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from .flow_models import FlowReportSummary, ProjectFlowReport, ReleaseCheckReport


class FlowCSVExporter:
    def export_flow_report(self, reports: List[ProjectFlowReport], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "project_path",
            "mr_iid",
            "title",
            "web_url",
            "source_branch",
            "target_branch",
            "merged_at",
            "merged_by",
            "jira_tickets",
            "route_status",
            "containment_status",
            "verified_by",
            "evidence",
            "backfill_required",
        ]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for report in reports:
                for a in report.assessments:
                    writer.writerow({
                        "project_path": a.project_path,
                        "mr_iid": a.mr_iid,
                        "title": a.title,
                        "web_url": a.web_url,
                        "source_branch": a.source_branch,
                        "target_branch": a.target_branch,
                        "merged_at": a.merged_at or "",
                        "merged_by": a.merged_by_username or "",
                        "jira_tickets": "|".join(a.jira_tickets),
                        "route_status": a.route_status,
                        "containment_status": a.containment_status,
                        "verified_by": a.verified_by,
                        "evidence": a.evidence,
                        "backfill_required": a.backfill_required,
                    })

    def export_release_check(self, report: ReleaseCheckReport, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "jira_ticket",
                    "status",
                    "projects",
                    "master_commits",
                    "premaster_commits",
                    "master_mrs",
                    "premaster_mrs",
                ],
            )
            writer.writeheader()
            for t in report.ticket_results:
                writer.writerow({
                    "jira_ticket": t.jira_ticket,
                    "status": t.status,
                    "projects": "|".join(t.projects),
                    "master_commits": "|".join(t.master_commits),
                    "premaster_commits": "|".join(t.premaster_commits),
                    "master_mrs": "|".join(str(x) for x in t.master_mrs),
                    "premaster_mrs": "|".join(str(x) for x in t.premaster_mrs),
                })


class FlowJSONExporter:
    def export_flow_report(
        self,
        reports: List[ProjectFlowReport],
        summary: FlowReportSummary,
        output_path: str,
    ) -> None:
        data = {
            "summary": summary.__dict__,
            "projects": [
                {
                    "project_path": r.project_path,
                    "premaster_ref": r.premaster_ref,
                    "error": r.error,
                    "assessments": [a.__dict__ for a in r.assessments],
                }
                for r in reports
            ],
        }
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def export_release_check(self, report: ReleaseCheckReport, output_path: str) -> None:
        data = {
            "scope_label": report.scope_label,
            "tickets": [t.__dict__ for t in report.ticket_results],
            "open_exceptions": report.open_exceptions,
        }
        Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")


class FlowHTMLExporter:
    def export_flow_report(
        self,
        reports: List[ProjectFlowReport],
        summary: FlowReportSummary,
        output_path: str,
    ) -> None:
        rows = []
        for report in reports:
            for a in report.assessments:
                cls = "violation" if a.route_status.startswith("VIOLATION") else ""
                if a.containment_status == "MISSING_ON_PREMASTER":
                    cls = "violation"
                rows.append(
                    f"<tr class='{cls}'><td>{a.project_path}</td><td><a href='{a.web_url}'>!{a.mr_iid}</a></td>"
                    f"<td>{a.source_branch}</td><td>{a.route_status}</td>"
                    f"<td>{a.containment_status}</td><td>{a.verified_by}</td>"
                    f"<td>{'|'.join(a.jira_tickets)}</td></tr>"
                )
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GitDoctor Flow Report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background: #f0f0f0; }}
.violation {{ background: #ffe0e0; }}
.summary {{ margin-bottom: 1.5rem; }}
</style></head><body>
<h1>Branch flow report</h1>
<div class="summary">
<p>MRs assessed: {summary.total_mrs} | Compliant: {summary.compliant} |
Violations: {summary.violations} | Exceptions: {summary.exceptions} |
Missing on premaster: {summary.missing_on_premaster}</p>
</div>
<table><thead><tr>
<th>Project</th><th>MR</th><th>Source</th><th>Route</th><th>Containment</th><th>Verified by</th><th>JIRA</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table>
</body></html>"""
        Path(output_path).write_text(html, encoding="utf-8")

    def export_release_check(self, report: ReleaseCheckReport, output_path: str) -> None:
        rows = []
        for t in report.ticket_results:
            cls = "violation" if t.status in ("MISSING_BOTH", "MASTER_ONLY") else ""
            rows.append(
                f"<tr class='{cls}'><td>{t.jira_ticket}</td><td>{t.status}</td>"
                f"<td>{', '.join(t.projects)}</td>"
                f"<td>{len(t.master_commits)}</td><td>{len(t.premaster_commits)}</td></tr>"
            )
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Release reconciliation</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; }}
.violation {{ background: #ffe0e0; }}
</style></head><body>
<h1>Release check: {report.scope_label}</h1>
<table><thead><tr><th>Ticket</th><th>Status</th><th>Projects</th><th>Master commits</th><th>Premaster commits</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>"""
        Path(output_path).write_text(html, encoding="utf-8")
