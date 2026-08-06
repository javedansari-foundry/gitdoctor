"""Tests for flow policy classification."""
from gitdoctor.flow_models import FlowPolicy
from gitdoctor.flow_policy import branch_matches_any_prefix, classify_mr_route
from gitdoctor.models import MergeRequest


def test_branch_prefix_match():
    assert branch_matches_any_prefix("premaster-291225", ["premaster"])
    assert branch_matches_any_prefix("feature/MON-1", ["feature/"])
    assert not branch_matches_any_prefix("hotfix/foo", ["premaster"])


def test_classify_compliant_premaster_to_master():
    policy = FlowPolicy()
    mr = MergeRequest(
        mr_id=1,
        mr_iid=10,
        title="MON-1",
        description="",
        state="merged",
        source_branch="premaster-291225",
        target_branch="master",
        author_name="a",
        author_username="a",
    )
    assert classify_mr_route(mr, policy) == "COMPLIANT"


def test_classify_violation_feature_to_master():
    policy = FlowPolicy()
    mr = MergeRequest(
        mr_id=1,
        mr_iid=11,
        title="MON-2",
        description="",
        state="merged",
        source_branch="feature/MON-2-fix",
        target_branch="master",
        author_name="a",
        author_username="a",
    )
    assert classify_mr_route(mr, policy) == "VIOLATION_DIRECT_FEATURE"


def test_classify_exception_label():
    policy = FlowPolicy(exception_labels=["flow-exception"])
    mr = MergeRequest(
        mr_id=1,
        mr_iid=12,
        title="MON-3",
        description="",
        state="merged",
        source_branch="feature/urgent",
        target_branch="master",
        author_name="a",
        author_username="a",
        labels=["flow-exception"],
    )
    assert classify_mr_route(mr, policy) == "EXCEPTION"
