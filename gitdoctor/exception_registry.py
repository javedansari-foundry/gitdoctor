"""Exception registry for audited feature→master bypasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import uuid

import yaml


@dataclass
class FlowExceptionRecord:
    exception_id: str
    project_path: str
    mr_iid: int
    jira_ticket: str
    reason: str
    requested_by: str = ""
    approved_by: str = ""
    approved_at: str = ""
    backfill_required: bool = True
    backfilled: bool = False
    backfill_mr_iid: Optional[int] = None
    master_merge_commit: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "exception_id": self.exception_id,
            "project_path": self.project_path,
            "mr_iid": self.mr_iid,
            "jira_ticket": self.jira_ticket,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "backfill_required": self.backfill_required,
            "backfilled": self.backfilled,
            "backfill_mr_iid": self.backfill_mr_iid,
            "master_merge_commit": self.master_merge_commit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlowExceptionRecord":
        return cls(
            exception_id=data.get("exception_id", ""),
            project_path=data.get("project_path", ""),
            mr_iid=int(data.get("mr_iid", 0)),
            jira_ticket=data.get("jira_ticket", ""),
            reason=data.get("reason", ""),
            requested_by=data.get("requested_by", ""),
            approved_by=data.get("approved_by", ""),
            approved_at=data.get("approved_at", ""),
            backfill_required=data.get("backfill_required", True),
            backfilled=data.get("backfilled", False),
            backfill_mr_iid=data.get("backfill_mr_iid"),
            master_merge_commit=data.get("master_merge_commit"),
        )


class ExceptionRegistry:
    def __init__(self, registry_dir: str | Path):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, record: FlowExceptionRecord) -> Path:
        safe_ticket = record.jira_ticket.replace("/", "-")
        return self.registry_dir / f"{safe_ticket}-{record.exception_id}.yaml"

    def register(
        self,
        project_path: str,
        mr_iid: int,
        jira_ticket: str,
        reason: str,
        requested_by: str = "",
        approved_by: str = "",
        master_merge_commit: Optional[str] = None,
    ) -> FlowExceptionRecord:
        record = FlowExceptionRecord(
            exception_id=f"EX-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            project_path=project_path,
            mr_iid=mr_iid,
            jira_ticket=jira_ticket.upper(),
            reason=reason,
            requested_by=requested_by,
            approved_by=approved_by,
            approved_at=datetime.now(timezone.utc).isoformat(),
            master_merge_commit=master_merge_commit,
        )
        path = self._path_for(record)
        with open(path, "w") as f:
            yaml.safe_dump(record.to_dict(), f, sort_keys=False)
        return record

    def list_all(self) -> List[FlowExceptionRecord]:
        records = []
        for path in sorted(self.registry_dir.glob("*.yaml")):
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            records.append(FlowExceptionRecord.from_dict(data))
        return records

    def list_open(self) -> List[FlowExceptionRecord]:
        return [r for r in self.list_all() if r.backfill_required and not r.backfilled]

    def close_backfill(
        self,
        exception_id: str,
        backfill_mr_iid: Optional[int] = None,
    ) -> Optional[FlowExceptionRecord]:
        for path in self.registry_dir.glob("*.yaml"):
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            if data.get("exception_id") == exception_id:
                data["backfilled"] = True
                if backfill_mr_iid:
                    data["backfill_mr_iid"] = backfill_mr_iid
                with open(path, "w") as f:
                    yaml.safe_dump(data, f, sort_keys=False)
                return FlowExceptionRecord.from_dict(data)
        return None

    def find_for_mr(self, project_path: str, mr_iid: int) -> Optional[FlowExceptionRecord]:
        for rec in self.list_all():
            if rec.project_path == project_path and rec.mr_iid == mr_iid:
                return rec
        return None
