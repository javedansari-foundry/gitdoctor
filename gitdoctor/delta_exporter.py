"""
Delta result exporters.

Handles exporting delta comparison results to various formats (CSV, JSON, HTML, etc.).
"""

import csv
import json
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from .models import DeltaResult, DeltaSummary


logger = logging.getLogger(__name__)


class DeltaCSVExporter:
    """
    Exports delta results to CSV format.
    
    CSV format matches the structure described in the PE team's guide,
    with all necessary columns for analysis.
    """
    
    # CSV column headers
    HEADERS = [
        "project_path",
        "project_name",
        "project_id",
        "project_web_url",
        "base_ref",
        "target_ref",
        "base_exists",
        "target_exists",
        "commit_sha",
        "short_id",
        "title",
        "message",
        "author_name",
        "author_email",
        "authored_date",
        "committed_date",
        "committer_name",
        "committer_email",
        "commit_web_url",
        "parent_shas",
        "jira_tickets",
        "jira_ticket_urls",
        "compare_timeout",
        "compare_same_ref",
        "error"
    ]
    
    def export(self, deltas: List[DeltaResult], output_path: str, jira_linker=None) -> None:
        """
        Export delta results to CSV file.
        
        Args:
            deltas: List of DeltaResult objects
            output_path: Path to output CSV file
            jira_linker: Optional JIRALinker instance for ticket extraction
            
        Raises:
            IOError: If file cannot be written
        """
        output_file = Path(output_path)
        
        logger.info(f"Exporting delta results to {output_path}")
        
        try:
            with output_file.open('w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.HEADERS)
                writer.writeheader()
                
                rows_written = 0
                
                for delta in deltas:
                    if delta.commits:
                        # Write one row per commit
                        for commit in delta.commits:
                            row = self._create_row(delta, commit, jira_linker)
                            writer.writerow(row)
                            rows_written += 1
                    else:
                        # Write one row for the project even if no commits
                        # This helps identify projects where refs don't exist or comparison failed
                        row = self._create_empty_row(delta)
                        writer.writerow(row)
                        rows_written += 1
                
            logger.info(f"Successfully exported {rows_written} rows to {output_path}")
            
        except IOError as e:
            logger.error(f"Failed to write CSV file: {e}")
            raise
    
    def _create_row(self, delta: DeltaResult, commit, jira_linker=None) -> dict:
        """Create a CSV row for a commit."""
        # Extract JIRA tickets if linker is provided
        jira_tickets = ""
        jira_ticket_urls = ""
        
        if jira_linker:
            tickets = jira_linker.extract_tickets_from_text(commit.title + " " + commit.message)
            if tickets:
                jira_tickets = "|".join(sorted(tickets))
                jira_ticket_urls = "|".join([jira_linker.get_ticket_url(t) for t in sorted(tickets)])
        
        return {
            "project_path": delta.project_path,
            "project_name": delta.project_name,
            "project_id": delta.project_id,
            "project_web_url": delta.project_web_url,
            "base_ref": delta.base_ref,
            "target_ref": delta.target_ref,
            "base_exists": delta.base_exists,
            "target_exists": delta.target_exists,
            "commit_sha": commit.commit_sha,
            "short_id": commit.short_id,
            "title": commit.title,
            "message": commit.message,
            "author_name": commit.author_name,
            "author_email": commit.author_email,
            "authored_date": commit.authored_date,
            "committed_date": commit.committed_date,
            "committer_name": commit.committer_name,
            "committer_email": commit.committer_email,
            "commit_web_url": commit.web_url,
            "parent_shas": "|".join(commit.parent_ids) if commit.parent_ids else "",
            "jira_tickets": jira_tickets,
            "jira_ticket_urls": jira_ticket_urls,
            "compare_timeout": delta.compare_timeout,
            "compare_same_ref": delta.compare_same_ref,
            "error": delta.error or ""
        }
    
    def _create_empty_row(self, delta: DeltaResult) -> dict:
        """Create a CSV row for a project with no commits (error or no changes)."""
        return {
            "project_path": delta.project_path,
            "project_name": delta.project_name,
            "project_id": delta.project_id,
            "project_web_url": delta.project_web_url,
            "base_ref": delta.base_ref,
            "target_ref": delta.target_ref,
            "base_exists": delta.base_exists,
            "target_exists": delta.target_exists,
            "commit_sha": "",
            "short_id": "",
            "title": "",
            "message": "",
            "author_name": "",
            "author_email": "",
            "authored_date": "",
            "committed_date": "",
            "committer_name": "",
            "committer_email": "",
            "commit_web_url": "",
            "parent_shas": "",
            "compare_timeout": delta.compare_timeout,
            "compare_same_ref": delta.compare_same_ref,
            "error": delta.error or ""
        }


class DeltaJSONExporter:
    """
    Exports delta results to JSON format.
    
    Useful for programmatic processing or integration with other tools.
    """
    
    def export(self, deltas: List[DeltaResult], output_path: str) -> None:
        """
        Export delta results to JSON file.
        
        Args:
            deltas: List of DeltaResult objects
            output_path: Path to output JSON file
            
        Raises:
            IOError: If file cannot be written
        """
        output_file = Path(output_path)
        
        logger.info(f"Exporting delta results to {output_path}")
        
        try:
            # Convert dataclasses to dictionaries
            data = []
            for delta in deltas:
                delta_dict = {
                    "project": {
                        "id": delta.project_id,
                        "name": delta.project_name,
                        "path": delta.project_path,
                        "web_url": delta.project_web_url
                    },
                    "comparison": {
                        "base_ref": delta.base_ref,
                        "target_ref": delta.target_ref,
                        "base_exists": delta.base_exists,
                        "target_exists": delta.target_exists,
                        "compare_timeout": delta.compare_timeout,
                        "compare_same_ref": delta.compare_same_ref
                    },
                    "statistics": {
                        "total_commits": delta.total_commits,
                        "filtered_commits": len(delta.commits),
                        "files_changed": delta.files_changed,
                        "total_additions": delta.total_additions,
                        "total_deletions": delta.total_deletions
                    },
                    "commits": [
                        {
                            "sha": commit.commit_sha,
                            "short_id": commit.short_id,
                            "title": commit.title,
                            "message": commit.message,
                            "author": {
                                "name": commit.author_name,
                                "email": commit.author_email,
                                "date": commit.authored_date
                            },
                            "committer": {
                                "name": commit.committer_name,
                                "email": commit.committer_email,
                                "date": commit.committed_date
                            },
                            "web_url": commit.web_url,
                            "parent_ids": commit.parent_ids
                        }
                        for commit in delta.commits
                    ],
                    "error": delta.error
                }
                data.append(delta_dict)
            
            with output_file.open('w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully exported {len(deltas)} delta results to {output_path}")
            
        except IOError as e:
            logger.error(f"Failed to write JSON file: {e}")
            raise


class DeltaHTMLExporter:
    """
    Exports delta results to a beautiful HTML report.
    
    Creates a self-contained HTML file with:
    - Summary statistics
    - Interactive tables
    - Charts and visualizations
    - Project breakdown
    - Author statistics
    """
    
    def export(self, deltas: List[DeltaResult], output_path: str, summary: DeltaSummary = None, jira_linker=None) -> None:
        """
        Export delta results to HTML file.
        
        Args:
            deltas: List of DeltaResult objects
            output_path: Path to output HTML file
            summary: Optional DeltaSummary for enhanced reporting
            jira_linker: Optional JIRALinker for ticket extraction
        """
        output_file = Path(output_path)
        
        logger.info(f"Exporting delta results to {output_path}")
        
        try:
            html_content = self._generate_html(deltas, summary, jira_linker)
            
            with output_file.open('w', encoding='utf-8') as htmlfile:
                htmlfile.write(html_content)
            
            logger.info(f"Successfully exported HTML report to {output_path}")
            
        except IOError as e:
            logger.error(f"Failed to write HTML file: {e}")
            raise
    
    def _generate_html(self, deltas: List[DeltaResult], summary: DeltaSummary = None, jira_linker=None) -> str:
        """Generate the complete HTML content."""
        
        # Collect statistics
        total_commits = sum(len(d.commits) for d in deltas)
        projects_with_changes = sum(1 for d in deltas if d.has_changes)
        projects_with_errors = sum(1 for d in deltas if d.error)
        
        # Get base and target refs
        base_ref = deltas[0].base_ref if deltas else "N/A"
        target_ref = deltas[0].target_ref if deltas else "N/A"
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitDoctor Delta Report: {base_ref} → {target_ref}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 GitDoctor Delta Report</h1>
            <p class="subtitle">Release Comparison Analysis</p>
        </header>
        
        <div class="summary-section">
            <h2>📊 Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{base_ref}</div>
                    <div class="stat-label">Base Reference</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{target_ref}</div>
                    <div class="stat-label">Target Reference</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(deltas)}</div>
                    <div class="stat-label">Projects Searched</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{projects_with_changes}</div>
                    <div class="stat-label">Projects with Changes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_commits}</div>
                    <div class="stat-label">Total Commits</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{projects_with_errors}</div>
                    <div class="stat-label">Projects with Errors</div>
                </div>
            </div>
        </div>
        
        {self._generate_projects_section(deltas)}
        {self._generate_commits_table(deltas, jira_linker)}
        {self._generate_jira_section(deltas, jira_linker) if jira_linker else ''}
        {self._generate_footer(timestamp)}
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_projects_section(self, deltas: List[DeltaResult]) -> str:
        """Generate projects breakdown section."""
        html = '<div class="projects-section"><h2>📁 Projects Breakdown</h2><div class="projects-grid">'
        
        for delta in deltas:
            status_class = "success" if delta.has_changes else ("error" if delta.error else "no-changes")
            status_icon = "✅" if delta.has_changes else ("❌" if delta.error else "⚪")
            
            html += f"""
            <div class="project-card {status_class}">
                <div class="project-header">
                    <h3>{status_icon} {delta.project_name}</h3>
                    <a href="{delta.project_web_url}" target="_blank" class="project-link">View in GitLab →</a>
                </div>
                <div class="project-path">{delta.project_path}</div>
                <div class="project-stats">
                    <span class="stat-badge">Commits: {len(delta.commits)}</span>
                    <span class="stat-badge">Files: {delta.files_changed}</span>
                </div>
                {f'<div class="error-message">⚠️ {delta.error}</div>' if delta.error else ''}
            </div>"""
        
        html += '</div></div>'
        return html
    
    def _generate_commits_table(self, deltas: List[DeltaResult], jira_linker=None) -> str:
        """Generate commits table section."""
        # Collect all commits
        all_commits = []
        for delta in deltas:
            for commit in delta.commits:
                all_commits.append((delta, commit))
        
        if not all_commits:
            return '<div class="commits-section"><h2>📝 Commits</h2><p class="no-data">No commits found in the delta range.</p></div>'
        
        html = f"""
        <div class="commits-section">
            <h2>📝 Commits ({len(all_commits)})</h2>
            <div class="table-container">
                <table class="commits-table">
                    <thead>
                        <tr>
                            <th>Project</th>
                            <th>Commit</th>
                            <th>Title</th>
                            <th>JIRA Tickets</th>
                            <th>Author</th>
                            <th>Date</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for delta, commit in all_commits[:100]:  # Limit to first 100 for performance
            commit_date = commit.committed_date[:10] if commit.committed_date else "N/A"
            
            # Extract JIRA tickets if linker is available
            jira_cell = ""
            if jira_linker:
                tickets = jira_linker.extract_tickets_from_text(commit.title + " " + commit.message)
                if tickets:
                    ticket_links = ", ".join([
                        f'<a href="{jira_linker.get_ticket_url(t)}" target="_blank">{t}</a>'
                        for t in sorted(tickets)
                    ])
                    jira_cell = f'<div class="jira-tickets">{ticket_links}</div>'
                else:
                    jira_cell = '<span class="no-tickets">-</span>'
            
            html += f"""
                        <tr>
                            <td><code>{delta.project_name}</code></td>
                            <td><code>{commit.short_id}</code></td>
                            <td>{self._escape_html(commit.title)}</td>
                            <td>{jira_cell}</td>
                            <td>{commit.author_name}</td>
                            <td>{commit_date}</td>
                            <td><a href="{commit.web_url}" target="_blank">View →</a></td>
                        </tr>"""
        
        if len(all_commits) > 100:
            html += f'<tr><td colspan="6" class="more-commits">... and {len(all_commits) - 100} more commits (see CSV for full list)</td></tr>'
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>"""
        
        return html
    
    def _generate_jira_section(self, deltas: List[DeltaResult], jira_linker) -> str:
        """Generate JIRA tickets summary section."""
        if not jira_linker:
            return ""
        
        ticket_summary = jira_linker.generate_ticket_summary(deltas)
        
        if not ticket_summary:
            return '<div class="jira-section"><h2>🎫 JIRA Tickets</h2><p class="no-data">No JIRA tickets found in commits.</p></div>'
        
        html = f"""
        <div class="jira-section">
            <h2>🎫 JIRA Tickets ({len(ticket_summary)})</h2>
            <div class="table-container">
                <table class="jira-table">
                    <thead>
                        <tr>
                            <th>Ticket</th>
                            <th>Commits</th>
                            <th>Projects</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for ticket_id, ticket_data in sorted(ticket_summary.items()):
            projects_list = ", ".join(ticket_data['projects'])
            html += f"""
                        <tr>
                            <td><strong>{ticket_id}</strong></td>
                            <td>{ticket_data['count']}</td>
                            <td>{projects_list}</td>
                            <td><a href="{ticket_data['url']}" target="_blank">View in JIRA →</a></td>
                        </tr>"""
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>"""
        
        return html
    
    def _generate_footer(self, timestamp: str) -> str:
        """Generate footer with timestamp."""
        return f"""
        <footer>
            <p>Generated by GitDoctor on {timestamp}</p>
            <p>For more details, see the CSV export</p>
        </footer>"""
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    
    def _get_css(self) -> str:
        """Get CSS styles for the HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .summary-section, .projects-section, .commits-section {
            padding: 30px 40px;
        }
        
        h2 {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .project-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background: #f9f9f9;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        
        .project-card.success {
            border-color: #4caf50;
            background: #f1f8f4;
        }
        
        .project-card.error {
            border-color: #f44336;
            background: #fff5f5;
        }
        
        .project-card.no-changes {
            border-color: #9e9e9e;
            background: #f5f5f5;
        }
        
        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .project-header h3 {
            font-size: 1.2em;
            color: #333;
        }
        
        .project-link {
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
        }
        
        .project-link:hover {
            text-decoration: underline;
        }
        
        .project-path {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }
        
        .project-stats {
            display: flex;
            gap: 10px;
        }
        
        .stat-badge {
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
        }
        
        .error-message {
            margin-top: 10px;
            padding: 10px;
            background: #ffebee;
            border-left: 4px solid #f44336;
            border-radius: 4px;
            color: #c62828;
            font-size: 0.9em;
        }
        
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
        }
        
        .commits-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .commits-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .commits-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .commits-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .commits-table tbody tr:hover {
            background: #f5f5f5;
        }
        
        .commits-table code {
            background: #f0f0f0;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .commits-table a {
            color: #667eea;
            text-decoration: none;
        }
        
        .commits-table a:hover {
            text-decoration: underline;
        }
        
        .more-commits {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px !important;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1em;
        }
        
        footer {
            background: #f5f5f5;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        
        footer p {
            margin: 5px 0;
        }
        
        .jira-section {
            padding: 30px 40px;
        }
        
        .jira-tickets {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .jira-tickets a {
            background: #0052CC;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .jira-tickets a:hover {
            background: #0065FF;
        }
        
        .no-tickets {
            color: #999;
            font-style: italic;
        }
        
        .jira-table {
            margin-top: 20px;
        }
        
        .jira-table td strong {
            color: #0052CC;
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactivity."""
        return """
        // Add any interactive features here
        document.addEventListener('DOMContentLoaded', function() {
            console.log('GitDoctor Delta Report loaded');
        });
        """


def get_exporter(format_type: str):
    """
    Get appropriate exporter based on format type.
    
    Args:
        format_type: One of 'csv', 'json', 'html'
        
    Returns:
        Exporter instance
        
    Raises:
        ValueError: If format_type is not supported
    """
    exporters = {
        'csv': DeltaCSVExporter,
        'json': DeltaJSONExporter,
        'html': DeltaHTMLExporter
    }
    
    if format_type not in exporters:
        raise ValueError(
            f"Unsupported format: {format_type}. "
            f"Supported formats: {', '.join(exporters.keys())}"
        )
    
    return exporters[format_type]()

