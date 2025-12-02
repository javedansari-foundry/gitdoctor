"""
Delta result exporters.

Handles exporting delta comparison results to various formats (CSV, JSON, HTML, etc.).
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from .models import DeltaResult, DeltaSummary


logger = logging.getLogger(__name__)


class DeltaCSVExporter:
    """
    Exports delta results to CSV format.
    
    CSV format matches the standard delta export structure,
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
    Exports delta results to a modern, interactive HTML report.
    
    Creates a self-contained HTML file with:
    - Tabbed navigation (Overview, By Project, By Author, Timeline)
    - Interactive search and filters
    - Visual charts for project and author breakdown
    - Collapsible project sections
    - JIRA ticket integration
    - Dark mode support
    - Export to CSV/JSON from within the report
    - Print-optimized stylesheet
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
    
    def _collect_statistics(self, deltas: List[DeltaResult], jira_linker=None) -> Dict[str, Any]:
        """Collect all statistics needed for the report."""
        stats = {
            'total_commits': 0,
            'projects_searched': len(deltas),
            'projects_with_changes': 0,
            'projects_with_errors': 0,
            'unique_authors': set(),
            'jira_tickets': set(),
            'commits_by_project': defaultdict(int),
            'commits_by_author': defaultdict(int),
            'commits_by_date': defaultdict(int),
            'all_commits': [],
            'ticket_summary': defaultdict(lambda: {'count': 0, 'projects': set(), 'commits': []})
        }
        
        for delta in deltas:
            if delta.has_changes:
                stats['projects_with_changes'] += 1
            if delta.error:
                stats['projects_with_errors'] += 1
            
            stats['commits_by_project'][delta.project_name] = len(delta.commits)
            stats['total_commits'] += len(delta.commits)
            
            for commit in delta.commits:
                stats['unique_authors'].add(commit.author_name)
                stats['commits_by_author'][commit.author_name] += 1
                
                # Extract date for timeline
                if commit.committed_date:
                    date_str = commit.committed_date[:10]
                    stats['commits_by_date'][date_str] += 1
                
                # Extract JIRA tickets
                if jira_linker:
                    tickets = jira_linker.extract_tickets_from_text(
                        commit.title + " " + commit.message
                    )
                    for ticket in tickets:
                        stats['jira_tickets'].add(ticket)
                        stats['ticket_summary'][ticket]['count'] += 1
                        stats['ticket_summary'][ticket]['projects'].add(delta.project_name)
                        stats['ticket_summary'][ticket]['commits'].append(commit.short_id)
                        stats['ticket_summary'][ticket]['url'] = jira_linker.get_ticket_url(ticket)
                
                # Store commit with project info
                stats['all_commits'].append({
                    'project_name': delta.project_name,
                    'project_path': delta.project_path,
                    'project_url': delta.project_web_url,
                    'sha': commit.commit_sha,
                    'short_id': commit.short_id,
                    'title': commit.title,
                    'message': commit.message,
                    'author': commit.author_name,
                    'email': commit.author_email,
                    'date': commit.committed_date,
                    'url': commit.web_url,
                    'tickets': list(jira_linker.extract_tickets_from_text(
                        commit.title + " " + commit.message
                    )) if jira_linker else []
                })
        
        # Sort commits by date (newest first)
        stats['all_commits'].sort(key=lambda x: x['date'] or '', reverse=True)
        
        # Convert sets to lists for JSON serialization
        stats['unique_authors'] = list(stats['unique_authors'])
        stats['jira_tickets'] = list(stats['jira_tickets'])
        
        # Convert ticket summary projects to lists
        for ticket_id in stats['ticket_summary']:
            stats['ticket_summary'][ticket_id]['projects'] = list(
                stats['ticket_summary'][ticket_id]['projects']
            )
        
        return stats
    
    def _generate_html(self, deltas: List[DeltaResult], summary: DeltaSummary = None, jira_linker=None) -> str:
        """Generate the complete HTML content."""
        
        # Get base and target refs
        base_ref = deltas[0].base_ref if deltas else "N/A"
        target_ref = deltas[0].target_ref if deltas else "N/A"
        
        # Collect statistics
        stats = self._collect_statistics(deltas, jira_linker)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data for JavaScript
        commits_json = json.dumps(stats['all_commits'], ensure_ascii=False)
        projects_data = json.dumps(dict(stats['commits_by_project']), ensure_ascii=False)
        authors_data = json.dumps(dict(stats['commits_by_author']), ensure_ascii=False)
        ticket_data = json.dumps(dict(stats['ticket_summary']), ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitDoctor Delta Report</title>
    <style>
{self._get_css()}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <div class="header-left">
                    <h1>🔍 GitDoctor</h1>
                    <span class="header-subtitle">Delta Report</span>
                </div>
                <div class="header-right">
                    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">
                        <span class="theme-icon">🌙</span>
                    </button>
                </div>
            </div>
            <div class="ref-badge-container">
                <div class="ref-badge base">
                    <span class="ref-label">BASE</span>
                    <span class="ref-value" title="{self._escape_html(base_ref)}">{self._escape_html(self._truncate(base_ref, 40))}</span>
                </div>
                <span class="ref-arrow">→</span>
                <div class="ref-badge target">
                    <span class="ref-label">TARGET</span>
                    <span class="ref-value" title="{self._escape_html(target_ref)}">{self._escape_html(self._truncate(target_ref, 40))}</span>
                </div>
            </div>
        </header>
        
        <!-- Summary Cards -->
        <section class="summary-cards">
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                    <div class="stat-value">{stats['total_commits']}</div>
                    <div class="stat-label">Total Commits</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📁</div>
                <div class="stat-info">
                    <div class="stat-value">{stats['projects_with_changes']}</div>
                    <div class="stat-label">Projects Changed</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-info">
                    <div class="stat-value">{len(stats['unique_authors'])}</div>
                    <div class="stat-label">Contributors</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🎫</div>
                <div class="stat-info">
                    <div class="stat-value">{len(stats['jira_tickets'])}</div>
                    <div class="stat-label">JIRA Tickets</div>
                </div>
            </div>
        </section>
        
        <!-- Tabs Navigation -->
        <nav class="tabs-nav">
            <button class="tab-btn active" data-tab="overview">📊 Overview</button>
            <button class="tab-btn" data-tab="projects">📁 By Project</button>
            <button class="tab-btn" data-tab="authors">👥 By Author</button>
            <button class="tab-btn" data-tab="timeline">📅 Timeline</button>
            {f'<button class="tab-btn" data-tab="jira">🎫 JIRA Tickets</button>' if jira_linker and stats['jira_tickets'] else ''}
        </nav>
        
        <!-- Search Bar -->
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search commits by SHA, message, author...">
            <select id="projectFilter" class="filter-select">
                <option value="">All Projects</option>
                {self._generate_project_options(deltas)}
            </select>
        </div>
        
        <!-- Tab Content -->
        <main class="tab-content">
            <!-- Overview Tab -->
            <div id="overview" class="tab-pane active">
                <div class="charts-grid">
                    <div class="chart-card">
                        <h3>📁 Commits by Project</h3>
                        <div class="chart-container" id="projectChart"></div>
                    </div>
                    <div class="chart-card">
                        <h3>👥 Top Contributors</h3>
                        <div class="chart-container" id="authorChart"></div>
                    </div>
                </div>
                
                {self._generate_quick_stats(stats)}
            </div>
            
            <!-- Projects Tab -->
            <div id="projects" class="tab-pane">
                <div class="projects-list">
                    {self._generate_projects_section(deltas, jira_linker)}
                </div>
            </div>
            
            <!-- Authors Tab -->
            <div id="authors" class="tab-pane">
                <div class="authors-list">
                    {self._generate_authors_section(deltas, stats)}
                </div>
            </div>
            
            <!-- Timeline Tab -->
            <div id="timeline" class="tab-pane">
                <div class="timeline-container" id="timelineContainer">
                    <!-- Populated by JavaScript -->
                </div>
                <div class="load-more" id="loadMore">
                    <button onclick="loadMoreCommits()">Load More Commits</button>
                </div>
            </div>
            
            <!-- JIRA Tab -->
            {self._generate_jira_tab(stats, jira_linker) if jira_linker and stats['jira_tickets'] else ''}
        </main>
        
        <!-- Footer -->
        <footer class="footer">
            <div class="footer-left">
                <span>Generated by GitDoctor on {timestamp}</span>
            </div>
            <div class="footer-right">
                <button class="export-btn" onclick="exportCSV()">📥 Export CSV</button>
                <button class="export-btn" onclick="exportJSON()">📥 Export JSON</button>
                <button class="export-btn" onclick="window.print()">🖨️ Print</button>
            </div>
        </footer>
    </div>
    
    <script>
        // Data
        const allCommits = {commits_json};
        const projectsData = {projects_data};
        const authorsData = {authors_data};
        const ticketData = {ticket_data};
        const baseRef = {json.dumps(base_ref)};
        const targetRef = {json.dumps(target_ref)};
        
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_project_options(self, deltas: List[DeltaResult]) -> str:
        """Generate project dropdown options."""
        options = ""
        for delta in sorted(deltas, key=lambda d: d.project_name):
            options += f'<option value="{self._escape_html(delta.project_name)}">{self._escape_html(delta.project_name)}</option>\n'
        return options
    
    def _generate_quick_stats(self, stats: Dict[str, Any]) -> str:
        """Generate quick stats section for overview."""
        # Top 5 projects
        top_projects = sorted(stats['commits_by_project'].items(), key=lambda x: x[1], reverse=True)[:5]
        # Top 5 authors
        top_authors = sorted(stats['commits_by_author'].items(), key=lambda x: x[1], reverse=True)[:5]
        
        html = '<div class="quick-stats">'
        
        # Top Projects
        html += '<div class="quick-stat-card"><h4>🏆 Top Projects</h4><ol class="ranked-list">'
        for project, count in top_projects:
            html += f'<li><span class="rank-name">{self._escape_html(project)}</span><span class="rank-count">{count}</span></li>'
        html += '</ol></div>'
        
        # Top Authors
        html += '<div class="quick-stat-card"><h4>🏆 Top Contributors</h4><ol class="ranked-list">'
        for author, count in top_authors:
            html += f'<li><span class="rank-name">{self._escape_html(author)}</span><span class="rank-count">{count}</span></li>'
        html += '</ol></div>'
        
        html += '</div>'
        return html
    
    def _generate_projects_section(self, deltas: List[DeltaResult], jira_linker=None) -> str:
        """Generate collapsible projects section."""
        html = ""
        
        # Sort by commit count descending
        sorted_deltas = sorted(deltas, key=lambda d: len(d.commits), reverse=True)
        
        for delta in sorted_deltas:
            commit_count = len(delta.commits)
            status_class = "success" if delta.has_changes else ("error" if delta.error else "neutral")
            status_icon = "✅" if delta.has_changes else ("❌" if delta.error else "⚪")
            
            html += f'''
            <div class="project-card {status_class}">
                <div class="project-header" onclick="toggleProject(this)">
                    <div class="project-title">
                        <span class="collapse-icon">▶</span>
                        <span class="status-icon">{status_icon}</span>
                        <h3>{self._escape_html(delta.project_name)}</h3>
                        <span class="commit-badge">{commit_count} commits</span>
                    </div>
                    <a href="{delta.project_web_url}" target="_blank" class="project-link" onclick="event.stopPropagation()">View in GitLab →</a>
                </div>
                <div class="project-path">{self._escape_html(delta.project_path)}</div>
                {f'<div class="error-msg">⚠️ {self._escape_html(delta.error)}</div>' if delta.error else ''}
                <div class="project-commits" style="display: none;">'''
            
            if delta.commits:
                html += '<table class="commits-mini-table"><thead><tr><th>SHA</th><th>Message</th><th>Author</th><th>Date</th></tr></thead><tbody>'
                for commit in delta.commits[:50]:  # Limit per project
                    date_str = commit.committed_date[:10] if commit.committed_date else "N/A"
                    
                    # Extract tickets
                    tickets_html = ""
                    if jira_linker:
                        tickets = jira_linker.extract_tickets_from_text(commit.title + " " + commit.message)
                        if tickets:
                            tickets_html = " ".join([
                                f'<a href="{jira_linker.get_ticket_url(t)}" class="ticket-badge" target="_blank">{t}</a>'
                                for t in sorted(tickets)
                            ])
                    
                    html += f'''<tr>
                        <td><a href="{commit.web_url}" target="_blank" class="sha-link">{commit.short_id}</a></td>
                        <td class="commit-msg">{self._escape_html(self._truncate(commit.title, 60))} {tickets_html}</td>
                        <td>{self._escape_html(commit.author_name)}</td>
                        <td>{date_str}</td>
                    </tr>'''
                
                if len(delta.commits) > 50:
                    html += f'<tr><td colspan="4" class="more-indicator">... and {len(delta.commits) - 50} more commits</td></tr>'
                
                html += '</tbody></table>'
            else:
                html += '<p class="no-commits">No commits in this project for the selected range.</p>'
            
            html += '</div></div>'
        
        return html
    
    def _generate_authors_section(self, deltas: List[DeltaResult], stats: Dict[str, Any]) -> str:
        """Generate authors breakdown section."""
        # Group commits by author
        author_commits = defaultdict(list)
        
        for delta in deltas:
            for commit in delta.commits:
                author_commits[commit.author_name].append({
                    'project': delta.project_name,
                    'sha': commit.short_id,
                    'title': commit.title,
                    'date': commit.committed_date,
                    'url': commit.web_url
                })
        
        # Sort authors by commit count
        sorted_authors = sorted(author_commits.items(), key=lambda x: len(x[1]), reverse=True)
        
        html = ""
        for author, commits in sorted_authors:
            html += f'''
            <div class="author-card">
                <div class="author-header" onclick="toggleAuthor(this)">
                    <div class="author-info">
                        <span class="collapse-icon">▶</span>
                        <div class="author-avatar">{self._get_initials(author)}</div>
                        <h3>{self._escape_html(author)}</h3>
                        <span class="commit-badge">{len(commits)} commits</span>
                    </div>
                </div>
                <div class="author-commits" style="display: none;">
                    <table class="commits-mini-table">
                        <thead><tr><th>Project</th><th>SHA</th><th>Message</th><th>Date</th></tr></thead>
                        <tbody>'''
            
            for c in commits[:30]:
                date_str = c['date'][:10] if c['date'] else "N/A"
                html += f'''<tr>
                    <td><code>{self._escape_html(c['project'])}</code></td>
                    <td><a href="{c['url']}" target="_blank" class="sha-link">{c['sha']}</a></td>
                    <td class="commit-msg">{self._escape_html(self._truncate(c['title'], 50))}</td>
                    <td>{date_str}</td>
                </tr>'''
            
            if len(commits) > 30:
                html += f'<tr><td colspan="4" class="more-indicator">... and {len(commits) - 30} more commits</td></tr>'
            
            html += '</tbody></table></div></div>'
        
        return html
    
    def _generate_jira_tab(self, stats: Dict[str, Any], jira_linker) -> str:
        """Generate JIRA tickets tab content."""
        if not jira_linker or not stats['jira_tickets']:
            return ''
        
        html = '''
        <div id="jira" class="tab-pane">
            <div class="jira-summary">
                <table class="jira-table">
                    <thead>
                        <tr>
                            <th>Ticket</th>
                            <th>Commits</th>
                            <th>Projects</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>'''
        
        # Sort tickets by commit count
        sorted_tickets = sorted(
            stats['ticket_summary'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for ticket_id, data in sorted_tickets:
            projects_str = ", ".join(data['projects'][:3])
            if len(data['projects']) > 3:
                projects_str += f" +{len(data['projects']) - 3} more"
            
            html += f'''
                <tr>
                    <td><strong class="ticket-id">{ticket_id}</strong></td>
                    <td>{data['count']}</td>
                    <td>{self._escape_html(projects_str)}</td>
                    <td><a href="{data['url']}" target="_blank" class="jira-link">View in JIRA →</a></td>
                </tr>'''
        
        html += '''
                    </tbody>
                </table>
            </div>
        </div>'''
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;"))
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if not text:
            return ""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
    
    def _get_initials(self, name: str) -> str:
        """Get initials from name."""
        if not name:
            return "?"
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[0].upper()
    
    def _get_css(self) -> str:
        """Get comprehensive CSS styles."""
        return """
        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f1f5f9;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --border-color: #e2e8f0;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.1);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
        }
        
        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: #334155;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.4);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.5);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .app-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .header {
            background: var(--accent-gradient);
            border-radius: var(--radius-lg);
            padding: 30px;
            margin-bottom: 24px;
            color: white;
            box-shadow: var(--shadow-lg);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .header-left {
            display: flex;
            align-items: baseline;
            gap: 12px;
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 700;
        }
        
        .header-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .theme-toggle {
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            cursor: pointer;
            font-size: 1.3rem;
            transition: all 0.2s;
        }
        
        .theme-toggle:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.1);
        }
        
        .ref-badge-container {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        
        .ref-badge {
            background: rgba(255,255,255,0.15);
            border-radius: var(--radius-md);
            padding: 12px 20px;
            backdrop-filter: blur(10px);
        }
        
        .ref-label {
            display: block;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.8;
            margin-bottom: 4px;
        }
        
        .ref-value {
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.95rem;
            font-weight: 600;
        }
        
        .ref-arrow {
            font-size: 1.5rem;
            opacity: 0.7;
        }
        
        /* Summary Cards */
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            border-radius: var(--radius-md);
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        
        .stat-icon {
            font-size: 2.5rem;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-primary);
        }
        
        .stat-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Tabs */
        .tabs-nav {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            background: var(--bg-secondary);
            padding: 8px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }
        
        .tab-btn {
            background: transparent;
            border: none;
            padding: 12px 20px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--text-secondary);
            transition: all 0.2s;
        }
        
        .tab-btn:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .tab-btn.active {
            background: var(--accent-gradient);
            color: white;
        }
        
        /* Search */
        .search-container {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        
        .search-input {
            flex: 1;
            min-width: 250px;
            padding: 14px 20px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            font-size: 1rem;
            background: var(--bg-secondary);
            color: var(--text-primary);
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .filter-select {
            padding: 14px 20px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            font-size: 1rem;
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            min-width: 180px;
        }
        
        /* Tab Content */
        .tab-content {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: 24px;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
            min-height: 500px;
        }
        
        .tab-pane {
            display: none;
        }
        
        .tab-pane.active {
            display: block;
        }
        
        /* Charts */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .chart-card {
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            padding: 20px;
        }
        
        .chart-card h3 {
            margin-bottom: 16px;
            font-size: 1.1rem;
            color: var(--text-primary);
        }
        
        .chart-container {
            height: 250px;
        }
        
        .bar-chart {
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .bar-item {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .bar-label {
            width: 120px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .bar-track {
            flex: 1;
            height: 24px;
            background: var(--bg-secondary);
            border-radius: var(--radius-sm);
            overflow: hidden;
        }
        
        .bar-fill {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: var(--radius-sm);
            transition: width 0.5s ease-out;
        }
        
        .bar-value {
            width: 40px;
            text-align: right;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        /* Quick Stats */
        .quick-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
        }
        
        .quick-stat-card {
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            padding: 20px;
        }
        
        .quick-stat-card h4 {
            margin-bottom: 16px;
            color: var(--text-primary);
        }
        
        .ranked-list {
            list-style: none;
            counter-reset: rank;
        }
        
        .ranked-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
            counter-increment: rank;
        }
        
        .ranked-list li::before {
            content: counter(rank) ".";
            font-weight: 600;
            color: var(--accent-primary);
            margin-right: 12px;
            min-width: 24px;
        }
        
        .rank-name {
            flex: 1;
            color: var(--text-primary);
        }
        
        .rank-count {
            font-weight: 600;
            color: var(--accent-primary);
            background: var(--bg-secondary);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        
        /* Project Cards */
        .project-card {
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            margin-bottom: 12px;
            border-left: 4px solid var(--border-color);
            overflow: hidden;
        }
        
        .project-card.success {
            border-left-color: var(--success);
        }
        
        .project-card.error {
            border-left-color: var(--error);
        }
        
        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .project-header:hover {
            background: var(--bg-secondary);
        }
        
        .project-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .collapse-icon {
            font-size: 0.8rem;
            color: var(--text-muted);
            transition: transform 0.2s;
        }
        
        .project-card.expanded .collapse-icon {
            transform: rotate(90deg);
        }
        
        .status-icon {
            font-size: 1rem;
        }
        
        .project-title h3 {
            font-size: 1rem;
            font-weight: 600;
        }
        
        .commit-badge {
            background: var(--accent-primary);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .project-link {
            color: var(--accent-primary);
            text-decoration: none;
            font-size: 0.9rem;
        }
        
        .project-link:hover {
            text-decoration: underline;
        }
        
        .project-path {
            padding: 0 20px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        
        .error-msg {
            margin: 0 20px 12px;
            padding: 12px;
            background: rgba(239, 68, 68, 0.1);
            border-radius: var(--radius-sm);
            color: var(--error);
            font-size: 0.9rem;
        }
        
        .project-commits {
            padding: 0 20px 20px;
        }
        
        .commits-mini-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        .commits-mini-table th {
            text-align: left;
            padding: 12px;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }
        
        .commits-mini-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .sha-link {
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent-primary);
            text-decoration: none;
        }
        
        .sha-link:hover {
            text-decoration: underline;
        }
        
        .commit-msg {
            max-width: 400px;
        }
        
        .ticket-badge {
            display: inline-block;
            background: #0052CC;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-decoration: none;
            margin-left: 8px;
        }
        
        .ticket-badge:hover {
            background: #0065FF;
        }
        
        .more-indicator {
            text-align: center;
            color: var(--text-muted);
            font-style: italic;
        }
        
        .no-commits {
            color: var(--text-muted);
            padding: 20px;
            text-align: center;
        }
        
        /* Author Cards */
        .author-card {
            background: var(--bg-tertiary);
            border-radius: var(--radius-md);
            margin-bottom: 12px;
            overflow: hidden;
        }
        
        .author-header {
            padding: 16px 20px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .author-header:hover {
            background: var(--bg-secondary);
        }
        
        .author-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .author-avatar {
            width: 40px;
            height: 40px;
            background: var(--accent-gradient);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .author-info h3 {
            flex: 1;
            font-size: 1rem;
        }
        
        .author-commits {
            padding: 0 20px 20px;
        }
        
        /* Timeline */
        .timeline-container {
            max-height: 600px;
            overflow-y: auto;
        }
        
        .timeline-item {
            display: flex;
            gap: 16px;
            padding: 16px 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .timeline-date {
            min-width: 100px;
            color: var(--text-muted);
            font-size: 0.85rem;
        }
        
        .timeline-content {
            flex: 1;
        }
        
        .timeline-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        
        .timeline-sha {
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent-primary);
            text-decoration: none;
            font-size: 0.9rem;
        }
        
        .timeline-project {
            background: var(--bg-tertiary);
            padding: 2px 10px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .timeline-title {
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .timeline-author {
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        
        .load-more {
            text-align: center;
            padding: 20px;
        }
        
        .load-more button {
            background: var(--accent-gradient);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: var(--radius-md);
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            transition: transform 0.2s;
        }
        
        .load-more button:hover {
            transform: scale(1.02);
        }
        
        /* JIRA Table */
        .jira-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .jira-table th {
            text-align: left;
            padding: 16px;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
        }
        
        .jira-table td {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .ticket-id {
            color: #0052CC;
        }
        
        .jira-link {
            color: var(--accent-primary);
            text-decoration: none;
        }
        
        .jira-link:hover {
            text-decoration: underline;
        }
        
        /* Footer */
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            margin-top: 24px;
            border-top: 1px solid var(--border-color);
            flex-wrap: wrap;
            gap: 16px;
        }
        
        .footer-left {
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        
        .footer-right {
            display: flex;
            gap: 12px;
        }
        
        .export-btn {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            padding: 10px 16px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 0.9rem;
            color: var(--text-primary);
            transition: all 0.2s;
        }
        
        .export-btn:hover {
            background: var(--accent-primary);
            color: white;
            border-color: var(--accent-primary);
        }
        
        /* Print Styles */
        @media print {
            body {
                background: white !important;
            }
            
            .header {
                background: #333 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            .theme-toggle,
            .search-container,
            .footer-right,
            .load-more {
                display: none !important;
            }
            
            .tab-pane {
                display: block !important;
                page-break-inside: avoid;
            }
            
            .tabs-nav {
                display: none;
            }
            
            .project-commits,
            .author-commits {
                display: block !important;
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                gap: 16px;
            }
            
            .ref-badge-container {
                flex-direction: column;
                align-items: stretch;
            }
            
            .ref-arrow {
                transform: rotate(90deg);
                text-align: center;
            }
            
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .footer {
                flex-direction: column;
                text-align: center;
            }
        }
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactivity."""
        return """
        // State
        let currentPage = 0;
        const pageSize = 50;
        let filteredCommits = [...allCommits];
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initTabs();
            initSearch();
            renderCharts();
            renderTimeline();
            
            // Check for saved theme
            const savedTheme = localStorage.getItem('gitdoctor-theme');
            if (savedTheme === 'dark') {
                document.body.setAttribute('data-theme', 'dark');
                document.querySelector('.theme-icon').textContent = '☀️';
            }
        });
        
        // Theme Toggle
        function toggleTheme() {
            const body = document.body;
            const icon = document.querySelector('.theme-icon');
            
            if (body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                icon.textContent = '🌙';
                localStorage.setItem('gitdoctor-theme', 'light');
            } else {
                body.setAttribute('data-theme', 'dark');
                icon.textContent = '☀️';
                localStorage.setItem('gitdoctor-theme', 'dark');
            }
        }
        
        // Tabs
        function initTabs() {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const tabId = btn.dataset.tab;
                    
                    // Update buttons
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    // Update panes
                    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                    document.getElementById(tabId).classList.add('active');
                });
            });
        }
        
        // Search & Filter
        function initSearch() {
            const searchInput = document.getElementById('searchInput');
            const projectFilter = document.getElementById('projectFilter');
            
            searchInput.addEventListener('input', debounce(filterCommits, 300));
            projectFilter.addEventListener('change', filterCommits);
        }
        
        function filterCommits() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const projectName = document.getElementById('projectFilter').value;
            
            filteredCommits = allCommits.filter(commit => {
                const matchesSearch = !searchTerm || 
                    commit.sha.toLowerCase().includes(searchTerm) ||
                    commit.short_id.toLowerCase().includes(searchTerm) ||
                    commit.title.toLowerCase().includes(searchTerm) ||
                    commit.author.toLowerCase().includes(searchTerm) ||
                    commit.message.toLowerCase().includes(searchTerm);
                
                const matchesProject = !projectName || commit.project_name === projectName;
                
                return matchesSearch && matchesProject;
            });
            
            currentPage = 0;
            renderTimeline();
        }
        
        // Charts
        function renderCharts() {
            renderBarChart('projectChart', projectsData, 8);
            renderBarChart('authorChart', authorsData, 8);
        }
        
        function renderBarChart(containerId, data, limit) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const sorted = Object.entries(data)
                .sort((a, b) => b[1] - a[1])
                .slice(0, limit);
            
            if (sorted.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">No data available</p>';
                return;
            }
            
            const maxValue = sorted[0][1];
            
            let html = '<div class="bar-chart">';
            sorted.forEach(([label, value]) => {
                const percentage = (value / maxValue) * 100;
                html += `
                    <div class="bar-item">
                        <div class="bar-label" title="${escapeHtml(label)}">${escapeHtml(truncate(label, 15))}</div>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="bar-value">${value}</div>
                    </div>
                `;
            });
            html += '</div>';
            
            container.innerHTML = html;
        }
        
        // Timeline
        function renderTimeline() {
            const container = document.getElementById('timelineContainer');
            if (!container) return;
            
            const start = 0;
            const end = (currentPage + 1) * pageSize;
            const commits = filteredCommits.slice(start, end);
            
            if (commits.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">No commits found matching your filters.</p>';
                document.getElementById('loadMore').style.display = 'none';
                return;
            }
            
            let html = '';
            commits.forEach(commit => {
                const date = commit.date ? commit.date.substring(0, 10) : 'N/A';
                const tickets = commit.tickets.map(t => 
                    `<a href="${ticketData[t]?.url || '#'}" class="ticket-badge" target="_blank">${t}</a>`
                ).join('');
                
                html += `
                    <div class="timeline-item">
                        <div class="timeline-date">${date}</div>
                        <div class="timeline-content">
                            <div class="timeline-header">
                                <a href="${commit.url}" class="timeline-sha" target="_blank">${commit.short_id}</a>
                                <span class="timeline-project">${escapeHtml(commit.project_name)}</span>
                                ${tickets}
                            </div>
                            <div class="timeline-title">${escapeHtml(commit.title)}</div>
                            <div class="timeline-author">by ${escapeHtml(commit.author)}</div>
                        </div>
                    </div>
                `;
            });
            
            container.innerHTML = html;
            
            // Show/hide load more
            const loadMore = document.getElementById('loadMore');
            loadMore.style.display = end < filteredCommits.length ? 'block' : 'none';
        }
        
        function loadMoreCommits() {
            currentPage++;
            renderTimeline();
        }
        
        // Project/Author Collapse
        function toggleProject(header) {
            const card = header.parentElement;
            const commits = card.querySelector('.project-commits');
            const isExpanded = card.classList.contains('expanded');
            
            card.classList.toggle('expanded');
            commits.style.display = isExpanded ? 'none' : 'block';
        }
        
        function toggleAuthor(header) {
            const card = header.parentElement;
            const commits = card.querySelector('.author-commits');
            const isExpanded = card.classList.contains('expanded');
            
            card.classList.toggle('expanded');
            commits.style.display = isExpanded ? 'none' : 'block';
        }
        
        // Export Functions
        function exportCSV() {
            const headers = ['Project', 'SHA', 'Title', 'Author', 'Date', 'URL', 'JIRA Tickets'];
            const rows = filteredCommits.map(c => [
                c.project_name,
                c.sha,
                `"${c.title.replace(/"/g, '""')}"`,
                c.author,
                c.date || '',
                c.url,
                c.tickets.join('; ')
            ]);
            
            const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
            downloadFile(csv, 'gitdoctor-delta-export.csv', 'text/csv');
        }
        
        function exportJSON() {
            const json = JSON.stringify(filteredCommits, null, 2);
            downloadFile(json, 'gitdoctor-delta-export.json', 'application/json');
        }
        
        function downloadFile(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }
        
        // Utilities
        function debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function truncate(text, maxLen) {
            if (!text) return '';
            return text.length > maxLen ? text.substring(0, maxLen - 3) + '...' : text;
        }
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
