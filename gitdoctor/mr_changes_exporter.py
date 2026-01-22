"""
Exporters for MR changes data - optimized for test selection.

Supports multiple output formats:
- JSON: Full structured data with all details
- CSV: Flat format for spreadsheet analysis
- Test Selection JSON: Optimized format for test automation tools
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from .models import MRChangesResult, CommitChange, FileChange


class MRChangesJSONExporter:
    """Export MR changes in full JSON format."""
    
    def export(self, result: MRChangesResult, output_path: str):
        """
        Export to JSON file with complete data.
        
        Args:
            result: MRChangesResult to export
            output_path: Path to output JSON file
        """
        data = {
            "mr_metadata": {
                "project_id": result.project_id,
                "project_name": result.project_name,
                "project_path": result.project_path,
                "project_web_url": result.project_web_url,
                "mr_iid": result.mr_iid,
                "mr_id": result.mr_id,
                "title": result.title,
                "description": result.description,
                "state": result.state,
                "source_branch": result.source_branch,
                "target_branch": result.target_branch,
                "author_name": result.author_name,
                "author_username": result.author_username,
                "merged_by_name": result.merged_by_name,
                "merged_at": result.merged_at,
                "created_at": result.created_at,
                "web_url": result.web_url,
                "merge_commit_sha": result.merge_commit_sha,
                "labels": result.labels,
            },
            "summary": {
                "total_commits": result.total_commits,
                "total_files_changed": result.total_files_changed,
                "files_by_extension": result.files_by_extension,
                "changed_directories": result.changed_directories,
                "jira_tickets": result.unique_jira_tickets,
            },
            "commits": [
                {
                    "commit_sha": commit.commit_sha,
                    "short_id": commit.short_id,
                    "title": commit.title,
                    "message": commit.message,
                    "author_name": commit.author_name,
                    "author_email": commit.author_email,
                    "created_at": commit.created_at,
                    "web_url": commit.web_url,
                    "jira_tickets": commit.jira_tickets,
                    "files_changed": commit.total_files_changed,
                    "files_added": commit.files_added,
                    "files_deleted": commit.files_deleted,
                    "files_modified": commit.files_modified,
                    "file_changes": [
                        {
                            "old_path": fc.old_path,
                            "new_path": fc.new_path,
                            "new_file": fc.new_file,
                            "deleted_file": fc.deleted_file,
                            "renamed_file": fc.renamed_file,
                            "is_test_file": fc.is_test_file,
                            "file_extension": fc.file_extension,
                            "diff": fc.diff if fc.diff else None,
                        }
                        for fc in commit.file_changes
                    ]
                }
                for commit in result.commits
            ],
            "all_file_changes": [
                {
                    "old_path": fc.old_path,
                    "new_path": fc.new_path,
                    "new_file": fc.new_file,
                    "deleted_file": fc.deleted_file,
                    "renamed_file": fc.renamed_file,
                    "is_test_file": fc.is_test_file,
                    "file_extension": fc.file_extension,
                }
                for fc in result.all_file_changes
            ],
            "error": result.error
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class MRChangesCSVExporter:
    """Export MR changes in CSV format (file-centric view)."""
    
    def export(self, result: MRChangesResult, output_path: str):
        """
        Export to CSV file with one row per file change.
        
        Args:
            result: MRChangesResult to export
            output_path: Path to output CSV file
        """
        fieldnames = [
            "mr_iid",
            "mr_title",
            "project_path",
            "source_branch",
            "target_branch",
            "state",
            "author",
            "merged_at",
            "file_path",
            "change_type",
            "is_test_file",
            "file_extension",
            "old_path",
            "jira_tickets",
            "total_commits",
            "mr_url",
            "error"
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            if result.error:
                # Write error row
                writer.writerow({
                    "mr_iid": result.mr_iid,
                    "mr_title": result.title,
                    "project_path": result.project_path,
                    "error": result.error
                })
            else:
                # Write one row per file
                for fc in result.all_file_changes:
                    change_type = "added" if fc.new_file else "deleted" if fc.deleted_file else "renamed" if fc.renamed_file else "modified"
                    
                    writer.writerow({
                        "mr_iid": result.mr_iid,
                        "mr_title": result.title,
                        "project_path": result.project_path,
                        "source_branch": result.source_branch,
                        "target_branch": result.target_branch,
                        "state": result.state,
                        "author": result.author_name,
                        "merged_at": result.merged_at or "",
                        "file_path": fc.new_path or fc.old_path,
                        "change_type": change_type,
                        "is_test_file": fc.is_test_file,
                        "file_extension": fc.file_extension,
                        "old_path": fc.old_path if fc.renamed_file else "",
                        "jira_tickets": "|".join(result.unique_jira_tickets),
                        "total_commits": result.total_commits,
                        "mr_url": result.web_url,
                        "error": ""
                    })


class TestSelectionExporter:
    """
    Export in optimized format for test selection tools.
    
    This format focuses on:
    - Changed source files (non-test files)
    - Changed directories
    - File patterns
    - JIRA tickets for test case tagging
    """
    
    def export(self, result: MRChangesResult, output_path: str):
        """
        Export to JSON optimized for test selection.
        
        Args:
            result: MRChangesResult to export
            output_path: Path to output JSON file
        """
        # Separate test files from source files
        source_files = result.get_non_test_files()
        test_files = result.get_test_files()
        
        data = {
            "test_selection": {
                "mr_info": {
                    "mr_iid": result.mr_iid,
                    "project_path": result.project_path,
                    "title": result.title,
                    "source_branch": result.source_branch,
                    "target_branch": result.target_branch,
                    "web_url": result.web_url,
                },
                "jira_tickets": result.unique_jira_tickets,
                "changed_source_files": [
                    {
                        "path": fc.new_path or fc.old_path,
                        "type": "added" if fc.new_file else "deleted" if fc.deleted_file else "modified",
                        "extension": fc.file_extension,
                    }
                    for fc in source_files
                ],
                "changed_test_files": [
                    {
                        "path": fc.new_path or fc.old_path,
                        "type": "added" if fc.new_file else "deleted" if fc.deleted_file else "modified",
                    }
                    for fc in test_files
                ],
                "changed_directories": result.changed_directories,
                "files_by_extension": result.files_by_extension,
                "statistics": {
                    "total_commits": result.total_commits,
                    "total_files_changed": result.total_files_changed,
                    "source_files_changed": len(source_files),
                    "test_files_changed": len(test_files),
                },
                "commits": [
                    {
                        "sha": commit.commit_sha,
                        "title": commit.title,
                        "author": commit.author_name,
                        "jira_tickets": commit.jira_tickets,
                    }
                    for commit in result.commits
                ]
            },
            "error": result.error
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class TestSelectionDetailedExporter:
    """
    Export detailed format for test selection with full diffs.
    
    Includes complete diff information for advanced test selection algorithms.
    """
    
    def export(self, result: MRChangesResult, output_path: str):
        """
        Export to JSON with full diffs for intelligent test selection.
        
        Args:
            result: MRChangesResult to export
            output_path: Path to output JSON file
        """
        # Separate test files from source files
        source_files = result.get_non_test_files()
        test_files = result.get_test_files()
        
        data = {
            "test_selection_detailed": {
                "mr_info": {
                    "mr_iid": result.mr_iid,
                    "project_id": result.project_id,
                    "project_path": result.project_path,
                    "project_name": result.project_name,
                    "title": result.title,
                    "description": result.description,
                    "source_branch": result.source_branch,
                    "target_branch": result.target_branch,
                    "author": result.author_name,
                    "merged_at": result.merged_at,
                    "labels": result.labels,
                    "web_url": result.web_url,
                },
                "jira_tickets": result.unique_jira_tickets,
                "changed_source_files": [
                    {
                        "path": fc.new_path or fc.old_path,
                        "old_path": fc.old_path,
                        "new_path": fc.new_path,
                        "type": "added" if fc.new_file else "deleted" if fc.deleted_file else "renamed" if fc.renamed_file else "modified",
                        "extension": fc.file_extension,
                        "diff": fc.diff,
                    }
                    for fc in source_files
                ],
                "changed_test_files": [
                    {
                        "path": fc.new_path or fc.old_path,
                        "old_path": fc.old_path,
                        "new_path": fc.new_path,
                        "type": "added" if fc.new_file else "deleted" if fc.deleted_file else "renamed" if fc.renamed_file else "modified",
                        "diff": fc.diff,
                    }
                    for fc in test_files
                ],
                "changed_directories": result.changed_directories,
                "files_by_extension": result.files_by_extension,
                "statistics": {
                    "total_commits": result.total_commits,
                    "total_files_changed": result.total_files_changed,
                    "source_files_changed": len(source_files),
                    "test_files_changed": len(test_files),
                },
                "commits": [
                    {
                        "sha": commit.commit_sha,
                        "short_id": commit.short_id,
                        "title": commit.title,
                        "message": commit.message,
                        "author": commit.author_name,
                        "author_email": commit.author_email,
                        "created_at": commit.created_at,
                        "web_url": commit.web_url,
                        "jira_tickets": commit.jira_tickets,
                        "files_changed": [
                            {
                                "path": fc.new_path or fc.old_path,
                                "type": "added" if fc.new_file else "deleted" if fc.deleted_file else "modified",
                                "is_test": fc.is_test_file,
                            }
                            for fc in commit.file_changes
                        ]
                    }
                    for commit in result.commits
                ]
            },
            "error": result.error
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def get_mr_changes_exporter(format_type: str):
    """
    Get the appropriate exporter for MR changes.
    
    Args:
        format_type: Export format - 'json', 'csv', 'test-selection', or 'test-selection-detailed'
    
    Returns:
        Exporter instance
    
    Raises:
        ValueError: If format is not supported
    """
    exporters = {
        'json': MRChangesJSONExporter(),
        'csv': MRChangesCSVExporter(),
        'test-selection': TestSelectionExporter(),
        'test-selection-detailed': TestSelectionDetailedExporter(),
    }
    
    if format_type not in exporters:
        raise ValueError(
            f"Unsupported format: {format_type}. "
            f"Supported formats: {', '.join(exporters.keys())}"
        )
    
    return exporters[format_type]

