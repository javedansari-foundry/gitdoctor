"""
JIRA integration for GitDoctor.

Extracts JIRA ticket references from commit messages and creates links.
"""

import re
import logging
from typing import List, Set, Dict, Optional
from urllib.parse import quote

from .models import DeltaCommit, DeltaResult


logger = logging.getLogger(__name__)


class JIRALinker:
    """
    Extracts JIRA ticket references from commit messages and creates links.
    
    Supports common JIRA ticket patterns:
    - MON-12345
    - JIRA-123
    - PROJECT-456
    """
    
    # Common JIRA ticket pattern: PROJECT-12345
    # Matches: uppercase letters/digits, dash, digits
    JIRA_PATTERN = re.compile(r'\b([A-Z][A-Z0-9]+-\d+)\b')
    
    def __init__(self, jira_base_url: str, project_key: Optional[str] = None):
        """
        Initialize JIRA linker.
        
        Args:
            jira_base_url: Base URL of JIRA instance (e.g., "https://jira.company.com")
            project_key: Optional project key to filter tickets (e.g., "MON")
                          If None, extracts all ticket patterns
        """
        self.jira_base_url = jira_base_url.rstrip('/')
        self.project_key = project_key.upper() if project_key else None
    
    def extract_tickets_from_commits(self, commits: List[DeltaCommit]) -> Dict[str, List[str]]:
        """
        Extract JIRA tickets from commit messages.
        
        Args:
            commits: List of DeltaCommit objects
            
        Returns:
            Dictionary mapping ticket ID to list of commit SHAs that reference it
            Example: {"MON-12345": ["abc123", "def456"]}
        """
        ticket_to_commits: Dict[str, List[str]] = {}
        
        for commit in commits:
            tickets = self.extract_tickets_from_text(commit.title + " " + commit.message)
            
            for ticket in tickets:
                if ticket not in ticket_to_commits:
                    ticket_to_commits[ticket] = []
                ticket_to_commits[ticket].append(commit.commit_sha)
        
        return ticket_to_commits
    
    def extract_tickets_from_text(self, text: str) -> Set[str]:
        """
        Extract JIRA ticket IDs from text.
        
        Args:
            text: Text to search (commit message, title, etc.)
            
        Returns:
            Set of unique ticket IDs found
        """
        if not text:
            return set()
        
        matches = self.JIRA_PATTERN.findall(text.upper())
        
        # Filter by project key if specified
        if self.project_key:
            matches = [t for t in matches if t.startswith(self.project_key + '-')]
        
        return set(matches)
    
    def get_ticket_url(self, ticket_id: str) -> str:
        """
        Get JIRA URL for a ticket.
        
        Args:
            ticket_id: JIRA ticket ID (e.g., "MON-12345")
            
        Returns:
            Full URL to the ticket
        """
        return f"{self.jira_base_url}/browse/{ticket_id}"
    
    def enrich_commit_with_jira_links(self, commit: DeltaCommit) -> Dict[str, str]:
        """
        Extract JIRA tickets from commit and return links.
        
        Args:
            commit: DeltaCommit object
            
        Returns:
            Dictionary mapping ticket ID to JIRA URL
            Example: {"MON-12345": "https://jira.company.com/browse/MON-12345"}
        """
        tickets = self.extract_tickets_from_text(commit.title + " " + commit.message)
        
        return {
            ticket: self.get_ticket_url(ticket)
            for ticket in tickets
        }
    
    def generate_ticket_summary(self, deltas: List[DeltaResult]) -> Dict[str, Dict[str, any]]:
        """
        Generate summary of JIRA tickets found across all deltas.
        
        Args:
            deltas: List of DeltaResult objects
            
        Returns:
            Dictionary with ticket summary:
            {
                "MON-12345": {
                    "url": "https://jira...",
                    "commits": ["abc123", "def456"],
                    "projects": ["project1", "project2"],
                    "count": 2
                }
            }
        """
        ticket_summary: Dict[str, Dict[str, any]] = {}
        
        for delta in deltas:
            for commit in delta.commits:
                tickets = self.extract_tickets_from_text(commit.title + " " + commit.message)
                
                for ticket in tickets:
                    if ticket not in ticket_summary:
                        ticket_summary[ticket] = {
                            "url": self.get_ticket_url(ticket),
                            "commits": [],
                            "projects": set(),
                            "count": 0
                        }
                    
                    ticket_summary[ticket]["commits"].append(commit.commit_sha)
                    ticket_summary[ticket]["projects"].add(delta.project_name)
                    ticket_summary[ticket]["count"] += 1
        
        # Convert sets to lists for JSON serialization
        for ticket_data in ticket_summary.values():
            ticket_data["projects"] = sorted(list(ticket_data["projects"]))
        
        return ticket_summary


def create_jira_linker(
    jira_base_url: Optional[str] = None,
    project_key: Optional[str] = None
) -> Optional[JIRALinker]:
    """
    Create a JIRA linker if base URL is provided.
    
    Args:
        jira_base_url: JIRA instance base URL
        project_key: Optional project key filter
        
    Returns:
        JIRALinker instance or None
    """
    if jira_base_url and jira_base_url.strip():
        return JIRALinker(jira_base_url.strip(), project_key)
    return None

