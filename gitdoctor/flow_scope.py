"""
Scope resolution and commit indexing for flow validation (separate from DeltaFinder).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .api_client import GitLabAPIError, GitLabClient, GitLabNotFound
from .config import FlowValidationConfig
from .flow_models import FlowPolicy, FlowValidationPreset
from .project_resolver import ProjectInfo
from .traceability import extract_jira_tickets


logger = logging.getLogger(__name__)


@dataclass
class IndexedCommit:
    sha: str
    short_id: str
    title: str
    message: str
    committed_date: str
    jira_tickets: List[str] = field(default_factory=list)
    web_url: str = ""


@dataclass
class ProjectCommitIndex:
    project_path: str
    project_id: int
    base_ref: str
    target_ref: str
    commits: List[IndexedCommit] = field(default_factory=list)
    commit_shas: Set[str] = field(default_factory=set)
    jira_to_shas: Dict[str, List[str]] = field(default_factory=dict)
    error: Optional[str] = None


def resolve_preset(config: FlowValidationConfig, preset_name: str) -> FlowValidationPreset:
    if preset_name not in config.presets:
        raise ValueError(
            f"Unknown preset '{preset_name}'. Available: {', '.join(config.presets.keys())}"
        )
    raw = config.presets[preset_name]
    policy_data = raw.get("policy", {})
    policy = FlowPolicy(
        premaster_prefix=policy_data.get("premaster_prefix", config.default_policy.premaster_prefix),
        feature_prefixes=policy_data.get("feature_prefixes", config.default_policy.feature_prefixes),
        allowed_master_sources=policy_data.get(
            "allowed_master_sources", config.default_policy.allowed_master_sources
        ),
        exception_labels=policy_data.get("exception_labels", config.default_policy.exception_labels),
        require_jira_in_commits=policy_data.get(
            "require_jira_in_commits", config.default_policy.require_jira_in_commits
        ),
    )
    return FlowValidationPreset(
        name=preset_name,
        projects=raw.get("projects", []),
        default_base_ref=raw.get("default_base_ref"),
        default_target_ref=raw.get("default_target_ref", "master"),
        premaster_ref=raw.get("premaster_ref"),
        policy=policy,
    )


def ref_exists(client: GitLabClient, project_id: int, ref: str) -> bool:
    try:
        client.get_tag(project_id, ref)
        return True
    except GitLabNotFound:
        pass
    except GitLabAPIError:
        pass
    try:
        client.get_branch(project_id, ref)
        return True
    except GitLabNotFound:
        pass
    except GitLabAPIError:
        pass
    try:
        client.get_commit(project_id, ref)
        return True
    except GitLabNotFound:
        return False
    except GitLabAPIError:
        return False


class FlowCommitIndexer:
    """Build commit index between base and target refs without using DeltaFinder."""

    def __init__(self, client: GitLabClient):
        self.client = client

    def index_project(
        self,
        project: ProjectInfo,
        base_ref: str,
        target_ref: str,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
    ) -> ProjectCommitIndex:
        result = ProjectCommitIndex(
            project_path=project.path_with_namespace,
            project_id=project.id,
            base_ref=base_ref,
            target_ref=target_ref,
        )
        try:
            if not ref_exists(self.client, project.id, base_ref):
                result.error = f"Base ref '{base_ref}' not found"
                return result
            if not ref_exists(self.client, project.id, target_ref):
                result.error = f"Target ref '{target_ref}' not found"
                return result

            target_commits = self.client.list_commits_from_ref(project.id, target_ref)
            base_shas = {c.get("id") for c in self.client.list_commits_from_ref(project.id, base_ref)}
            target_map = {c.get("id"): c for c in target_commits}
            delta_shas = set(target_map.keys()) - base_shas

            for sha in delta_shas:
                data = target_map[sha]
                committed = data.get("committed_date", "")
                if after_date and committed and committed < after_date:
                    continue
                if before_date and committed and committed > before_date:
                    continue
                text = f"{data.get('title', '')} {data.get('message', '')}"
                tickets = extract_jira_tickets(text)
                ic = IndexedCommit(
                    sha=sha,
                    short_id=data.get("short_id", sha[:8]),
                    title=data.get("title", ""),
                    message=data.get("message", ""),
                    committed_date=committed,
                    jira_tickets=tickets,
                    web_url=data.get("web_url", ""),
                )
                result.commits.append(ic)
                result.commit_shas.add(sha)
                for t in tickets:
                    result.jira_to_shas.setdefault(t, []).append(sha)

            result.commits.sort(key=lambda c: c.committed_date, reverse=True)
        except GitLabAPIError as e:
            result.error = str(e)
        except Exception as e:
            result.error = str(e)
        return result

    def build_premaster_sha_set(
        self,
        project_id: int,
        premaster_ref: str,
        limit_commits: Optional[int] = None,
    ) -> Set[str]:
        commits = self.client.list_commits_from_ref(project_id, premaster_ref)
        shas = {c.get("id") for c in commits if c.get("id")}
        if limit_commits and len(commits) > limit_commits:
            shas = {c.get("id") for c in commits[:limit_commits] if c.get("id")}
        return shas
