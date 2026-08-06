"""Branch naming policy helpers for flow validation."""
from __future__ import annotations

from typing import List, Optional

from .flow_models import FlowPolicy
from .models import MergeRequest


def branch_matches_any_prefix(branch_name: str, prefixes: List[str]) -> bool:
    if not branch_name:
        return False
    for prefix in prefixes:
        if prefix.endswith("/"):
            if branch_name.startswith(prefix) or branch_name == prefix.rstrip("/"):
                return True
        elif branch_name == prefix or branch_name.startswith(prefix):
            return True
    return False


def classify_mr_route(mr: MergeRequest, policy: FlowPolicy, target: str = "master") -> str:
    """Classify merge request source branch against policy."""
    src = mr.source_branch or ""
    tgt = mr.target_branch or ""

    if tgt != target and target:
        return "NOT_TARGET_BRANCH"

    if any(label in (mr.labels or []) for label in policy.exception_labels):
        return "EXCEPTION"

    if branch_matches_any_prefix(src, policy.allowed_master_sources):
        return "COMPLIANT"

    if branch_matches_any_prefix(src, policy.feature_prefixes):
        return "VIOLATION_DIRECT_FEATURE"

    return "VIOLATION_OTHER"


def classify_premaster_mr_route(mr: MergeRequest, policy: FlowPolicy) -> str:
    src = mr.source_branch or ""
    if any(label in (mr.labels or []) for label in policy.exception_labels):
        return "EXCEPTION"
    if branch_matches_any_prefix(src, policy.allowed_premaster_sources):
        return "COMPLIANT"
    return "VIOLATION_OTHER"
