"""
Tests for delta exporters with traceability fields.
"""

import csv
import json

from gitdoctor.delta_exporter import DeltaCSVExporter, DeltaJSONExporter
from gitdoctor.models import (
    DeltaResult,
    DeltaCommit,
    CommitTraceability,
    SourceCommitTrace,
)


def _build_delta_with_traceability():
    source_commit = SourceCommitTrace(
        source_commit_sha="source123",
        short_id="source12",
        title="MON-123 source",
        message="MON-123 source details",
        author_name="Source Dev",
        author_email="source@example.com",
        committed_date="2025-09-09T10:00:00Z",
        web_url="https://gitlab.example.com/group/project/commit/source123",
        jira_tickets=["MON-123"],
    )
    traceability = CommitTraceability(
        status="expanded",
        mr_project_path="group/project",
        mr_iid=42,
        mr_web_url="https://gitlab.example.com/group/project/-/merge_requests/42",
        source_commits=[source_commit],
        source_jira_tickets=["MON-123"],
    )
    commit = DeltaCommit(
        commit_sha="promoted123",
        short_id="promoted",
        title="MON-123 squash",
        message="MON-123 See merge request group/project!42",
        author_name="Release Bot",
        author_email="bot@example.com",
        authored_date="2025-09-10T10:00:00Z",
        committed_date="2025-09-10T10:00:00Z",
        committer_name="Release Bot",
        committer_email="bot@example.com",
        web_url="https://gitlab.example.com/group/project/commit/promoted123",
        parent_ids=[],
        traceability=traceability,
    )
    return DeltaResult(
        project_id=1,
        project_name="project",
        project_path="group/project",
        project_web_url="https://gitlab.example.com/group/project",
        base_ref="v1",
        target_ref="v2",
        base_exists=True,
        target_exists=True,
        commits=[commit],
    )


def test_csv_export_includes_traceability_columns(tmp_path):
    """CSV export should include traceability columns when present."""
    delta = _build_delta_with_traceability()
    output = tmp_path / "delta.csv"

    exporter = DeltaCSVExporter()
    exporter.export([delta], str(output))

    with output.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["traceability_status"] == "expanded"
    assert rows[0]["mr_iid"] == "42"
    assert rows[0]["source_commit_sha"] == "source123"
    assert rows[0]["source_jira_tickets"] == "MON-123"


def test_json_export_includes_traceability_payload(tmp_path):
    """JSON export should include nested traceability details."""
    delta = _build_delta_with_traceability()
    output = tmp_path / "delta.json"

    exporter = DeltaJSONExporter()
    exporter.export([delta], str(output))

    data = json.loads(output.read_text(encoding="utf-8"))
    traceability = data[0]["commits"][0]["traceability"]
    assert traceability["status"] == "expanded"
    assert traceability["mr_iid"] == 42
    assert traceability["source_commits"][0]["sha"] == "source123"
