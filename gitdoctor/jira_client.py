"""JIRA REST API and CSV import for release scope."""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import List, Optional, Set

import requests


logger = logging.getLogger(__name__)


class JiraClientError(Exception):
    pass


class JiraClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({"Accept": "application/json"})

    def search_issues(self, jql: str, max_results: int = 1000) -> List[dict]:
        issues = []
        start_at = 0
        page_size = 100
        while start_at < max_results:
            url = f"{self.base_url}/rest/api/3/search"
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": min(page_size, max_results - start_at),
                "fields": "key,summary,status",
            }
            resp = self.session.get(url, params=params, timeout=60)
            if resp.status_code == 401:
                raise JiraClientError("JIRA authentication failed")
            if not resp.ok:
                raise JiraClientError(f"JIRA search failed: {resp.status_code} {resp.text[:200]}")
            data = resp.json()
            batch = data.get("issues", [])
            issues.extend(batch)
            if start_at + len(batch) >= data.get("total", 0) or not batch:
                break
            start_at += len(batch)
        return issues

    @staticmethod
    def issue_keys(issues: List[dict]) -> List[str]:
        return [i.get("key", "").upper() for i in issues if i.get("key")]


def load_ticket_keys_from_csv(csv_path: str | Path) -> List[str]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"JIRA CSV not found: {path}")
    keys: Set[str] = set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise JiraClientError("CSV has no headers")
        key_col = None
        for name in reader.fieldnames:
            if name.lower() in ("key", "issue key", "issue_key", "jira", "ticket"):
                key_col = name
                break
        if not key_col:
            key_col = reader.fieldnames[0]
        for row in reader:
            val = (row.get(key_col) or "").strip().upper()
            if val and "-" in val:
                keys.add(val)
    return sorted(keys)


def resolve_release_ticket_keys(
    jira_csv: Optional[str] = None,
    jira_jql: Optional[str] = None,
    jira_client: Optional[JiraClient] = None,
) -> List[str]:
    keys: Set[str] = set()
    if jira_csv:
        keys.update(load_ticket_keys_from_csv(jira_csv))
    if jira_jql and jira_client:
        issues = jira_client.search_issues(jira_jql)
        keys.update(JiraClient.issue_keys(issues))
    elif jira_jql and not jira_client:
        raise JiraClientError("JIRA JQL provided but JIRA API credentials are not configured")
    return sorted(keys)
