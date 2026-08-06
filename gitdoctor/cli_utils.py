"""Shared CLI helpers (used by cli and flow_handlers to avoid circular imports)."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD (e.g., 2025-09-01)"
        )


def filter_projects_by_cli_args(
    projects: List,
    project_paths: Optional[str] = None,
    project_ids: Optional[str] = None,
) -> List:
    logger = logging.getLogger(__name__)
    if not project_paths and not project_ids:
        return projects
    filtered = []
    if project_paths:
        paths = [p.strip() for p in project_paths.split(",")]
        path_set = set(paths)
        for project in projects:
            if project.path_with_namespace in path_set:
                filtered.append(project)
        logger.info(f"Filtered to {len(filtered)} project(s) by path: {', '.join(paths)}")
        return filtered
    if project_ids:
        try:
            ids = [int(id_str.strip()) for id_str in project_ids.split(",")]
            id_set = set(ids)
            for project in projects:
                if project.id in id_set:
                    filtered.append(project)
            logger.info(f"Filtered to {len(filtered)} project(s) by ID")
            return filtered
        except ValueError as e:
            raise ValueError(f"Invalid project IDs: {project_ids}") from e
    return projects


def validate_date_range(
    after_date: Optional[str], before_date: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    after_date_iso = None
    before_date_iso = None
    after_dt = None
    if after_date:
        after_dt = parse_date(after_date)
        after_date_iso = after_dt.strftime("%Y-%m-%dT00:00:00Z")
    if before_date:
        before_dt = parse_date(before_date)
        before_date_iso = before_dt.strftime("%Y-%m-%dT23:59:59Z")
        if after_date and after_dt >= before_dt:
            raise ValueError(
                f"Invalid date range: --after ({after_dt.date()}) must be before --before ({before_dt.date()})"
            )
    return after_date_iso, before_date_iso
