"""
Sprint velocity exporters — CSV, JSON, and HTML reports.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import List

from .models import SprintProjectResult, SprintSummary


logger = logging.getLogger(__name__)


class SprintCSVExporter:
    """Export sprint commit detail and optional velocity summary CSV."""

    DETAIL_HEADERS = [
        "project_path",
        "project_name",
        "project_id",
        "ref_name",
        "commit_sha",
        "short_id",
        "title",
        "author_name",
        "author_email",
        "authored_date",
        "committed_date",
        "commit_web_url",
        "error",
    ]

    def export(
        self,
        results: List[SprintProjectResult],
        output_path: str,
        summary: SprintSummary | None = None,
    ) -> None:
        output_file = Path(output_path)
        logger.info(f"Exporting sprint commits to {output_path}")

        with output_file.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.DETAIL_HEADERS)
            writer.writeheader()

            for result in results:
                if result.error and not result.commits:
                    writer.writerow(
                        {
                            "project_path": result.project_path,
                            "project_name": result.project_name,
                            "project_id": result.project_id,
                            "ref_name": result.ref_name,
                            "error": result.error,
                        }
                    )
                    continue

                for commit in result.commits:
                    writer.writerow(
                        {
                            "project_path": result.project_path,
                            "project_name": result.project_name,
                            "project_id": result.project_id,
                            "ref_name": result.ref_name,
                            "commit_sha": commit.commit_sha,
                            "short_id": commit.short_id,
                            "title": commit.title,
                            "author_name": commit.author_name,
                            "author_email": commit.author_email,
                            "authored_date": commit.authored_date,
                            "committed_date": commit.committed_date,
                            "commit_web_url": commit.web_url,
                        }
                    )

        if summary:
            summary_path = str(output_file.with_stem(output_file.stem + "-velocity"))
            self._export_velocity_csv(summary, summary_path)

    def _export_velocity_csv(self, summary: SprintSummary, output_path: str) -> None:
        logger.info(f"Exporting velocity summary to {output_path}")
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["metric", "key", "value"])
            writer.writerow(["total_commits", "", summary.total_commits])
            writer.writerow(["unique_developers", "", len(summary.unique_developers)])
            for dev, count in sorted(
                summary.commits_by_developer.items(), key=lambda x: (-x[1], x[0])
            ):
                writer.writerow(["commits_by_developer", dev, count])
            for project, count in sorted(
                summary.commits_by_project.items(), key=lambda x: (-x[1], x[0])
            ):
                writer.writerow(["commits_by_project", project, count])
            for dev, projects in sorted(summary.velocity_matrix.items()):
                for project, count in sorted(projects.items(), key=lambda x: (-x[1], x[0])):
                    writer.writerow(["velocity_matrix", f"{dev} | {project}", count])


class SprintJSONExporter:
    def export(
        self,
        results: List[SprintProjectResult],
        output_path: str,
        summary: SprintSummary | None = None,
    ) -> None:
        payload = {
            "summary": _summary_to_dict(summary) if summary else None,
            "projects": [
                {
                    "project_path": r.project_path,
                    "project_name": r.project_name,
                    "project_id": r.project_id,
                    "ref_name": r.ref_name,
                    "error": r.error,
                    "commits": [
                        {
                            "commit_sha": c.commit_sha,
                            "short_id": c.short_id,
                            "title": c.title,
                            "author_name": c.author_name,
                            "author_email": c.author_email,
                            "authored_date": c.authored_date,
                            "committed_date": c.committed_date,
                            "web_url": c.web_url,
                        }
                        for c in r.commits
                    ],
                }
                for r in results
            ],
        }
        Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info(f"Exported sprint JSON to {output_path}")


class SprintHTMLExporter:
    def export(
        self,
        results: List[SprintProjectResult],
        output_path: str,
        summary: SprintSummary,
    ) -> None:
        html = self._generate_html(results, summary)
        Path(output_path).write_text(html, encoding="utf-8")
        logger.info(f"Exported sprint HTML report to {output_path}")

    def _generate_html(
        self, results: List[SprintProjectResult], summary: SprintSummary
    ) -> str:
        total = summary.total_commits or 1
        dev_rows = "".join(
            f"<tr><td>{dev}</td><td>{count}</td>"
            f"<td>{count / total * 100:.1f}%</td></tr>"
            for dev, count in sorted(
                summary.commits_by_developer.items(), key=lambda x: (-x[1], x[0])
            )
        )
        project_rows = "".join(
            f"<tr><td>{project}</td><td>{count}</td></tr>"
            for project, count in sorted(
                summary.commits_by_project.items(), key=lambda x: (-x[1], x[0])
            )
        )

        matrix_projects = sorted(
            {p for projects in summary.velocity_matrix.values() for p in projects}
        )
        matrix_header = "".join(f"<th>{p.split('/')[-1]}</th>" for p in matrix_projects)
        matrix_rows = ""
        for dev in sorted(summary.velocity_matrix.keys()):
            cells = "".join(
                f"<td>{summary.velocity_matrix[dev].get(p, 0) or ''}</td>"
                for p in matrix_projects
            )
            total = summary.commits_by_developer.get(dev, 0)
            matrix_rows += f"<tr><td><strong>{dev}</strong></td>{cells}<td><strong>{total}</strong></td></tr>"

        commit_rows = ""
        for result in results:
            for commit in result.commits:
                commit_rows += (
                    f"<tr>"
                    f"<td>{result.project_path}</td>"
                    f"<td>{commit.author_name}</td>"
                    f"<td><a href='{commit.web_url}'>{commit.short_id}</a></td>"
                    f"<td>{commit.title}</td>"
                    f"<td>{commit.committed_date[:10] if commit.committed_date else ''}</td>"
                    f"</tr>"
                )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sprint Velocity Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; color: #1a1a1a; }}
    h1, h2 {{ color: #2c3e50; }}
    .stats {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0; }}
    .stat-card {{ background: #f4f6f8; border-radius: 8px; padding: 1rem 1.5rem; min-width: 140px; }}
    .stat-card .value {{ font-size: 2rem; font-weight: 700; color: #2980b9; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background: #34495e; color: white; }}
    tr:nth-child(even) {{ background: #f9f9f9; }}
    .matrix td {{ text-align: center; }}
    .meta {{ color: #666; margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>Sprint Velocity Report</h1>
  <p class="meta">
    <strong>Branch:</strong> {summary.ref_name} &nbsp;|&nbsp;
    <strong>Window:</strong> {summary.date_range_start} → {summary.date_range_end} &nbsp;|&nbsp;
    <strong>Scope:</strong> {summary.scope}
  </p>

  <div class="stats">
    <div class="stat-card"><div class="value">{summary.total_commits}</div>Total Commits</div>
    <div class="stat-card"><div class="value">{len(summary.unique_developers)}</div>Developers</div>
    <div class="stat-card"><div class="value">{summary.projects_with_commits}</div>Active Repos</div>
    <div class="stat-card"><div class="value">{summary.total_projects}</div>Repos Scanned</div>
  </div>

  <h2>Velocity by Developer</h2>
  <table>
    <thead><tr><th>Developer</th><th>Commits</th><th>% of Sprint</th></tr></thead>
    <tbody>{dev_rows}</tbody>
  </table>

  <h2>Commits by Microservice / Repo</h2>
  <table>
    <thead><tr><th>Project</th><th>Commits</th></tr></thead>
    <tbody>{project_rows}</tbody>
  </table>

  <h2>Developer × Microservice Matrix</h2>
  <table class="matrix">
    <thead><tr><th>Developer</th>{matrix_header}<th>Total</th></tr></thead>
    <tbody>{matrix_rows}</tbody>
  </table>

  <h2>All Commits</h2>
  <table>
    <thead><tr><th>Project</th><th>Author</th><th>Commit</th><th>Title</th><th>Date</th></tr></thead>
    <tbody>{commit_rows}</tbody>
  </table>
</body>
</html>"""


def _summary_to_dict(summary: SprintSummary) -> dict:
    return {
        "ref_name": summary.ref_name,
        "date_range_start": summary.date_range_start,
        "date_range_end": summary.date_range_end,
        "scope": summary.scope,
        "total_projects": summary.total_projects,
        "projects_with_commits": summary.projects_with_commits,
        "projects_with_errors": summary.projects_with_errors,
        "total_commits": summary.total_commits,
        "unique_developers": summary.unique_developers,
        "commits_by_developer": summary.commits_by_developer,
        "commits_by_project": summary.commits_by_project,
        "velocity_matrix": summary.velocity_matrix,
    }


def get_sprint_exporter(format_type: str):
    exporters = {
        "csv": SprintCSVExporter,
        "json": SprintJSONExporter,
        "html": SprintHTMLExporter,
    }
    if format_type not in exporters:
        raise ValueError(f"Unsupported format: {format_type}")
    return exporters[format_type]()
