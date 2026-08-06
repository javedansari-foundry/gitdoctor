"""Tests for exception registry."""
from pathlib import Path

from gitdoctor.exception_registry import ExceptionRegistry


def test_register_and_list(tmp_path: Path):
    reg = ExceptionRegistry(tmp_path)
    rec = reg.register(
        project_path="dfs-core/devops/ansible_configs",
        mr_iid=99,
        jira_ticket="MON-100",
        reason="premaster unstable",
        approved_by="maintainer",
    )
    assert rec.exception_id.startswith("EX-")
    all_recs = reg.list_all()
    assert len(all_recs) == 1
    assert reg.list_open()[0].jira_ticket == "MON-100"


def test_close_backfill(tmp_path: Path):
    reg = ExceptionRegistry(tmp_path)
    rec = reg.register(
        project_path="p",
        mr_iid=1,
        jira_ticket="MON-1",
        reason="test",
    )
    closed = reg.close_backfill(rec.exception_id, backfill_mr_iid=200)
    assert closed.backfilled is True
    assert closed.backfill_mr_iid == 200
    assert reg.list_open() == []
