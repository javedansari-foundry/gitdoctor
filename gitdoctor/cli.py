"""
Command-line interface for GitDoctor.
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from . import __version__
from .config import load_config, ConfigError
from .api_client import GitLabClient, GitLabAPIError
from .project_resolver import resolve_projects
from .commit_finder import CommitFinder, CommitSearchResult, load_commit_shas_from_file
from .delta_finder import DeltaFinder
from .delta_exporter import get_exporter
from .models import DeltaSummary
from .jira_integration import create_jira_linker
from .notifications import create_slack_notifier, create_teams_notifier


# Configure logging
def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD (e.g., 2025-09-01)"
        )


def filter_projects_by_cli_args(
    projects: List,
    project_paths: Optional[str] = None,
    project_ids: Optional[str] = None
) -> List:
    """
    Filter projects based on CLI arguments.
    
    Args:
        projects: List of ProjectInfo objects from config
        project_paths: Comma-separated project paths (e.g., "path1,path2")
        project_ids: Comma-separated project IDs (e.g., "123,456")
        
    Returns:
        Filtered list of ProjectInfo objects
    """
    logger = logging.getLogger(__name__)
    
    if not project_paths and not project_ids:
        return projects
    
    filtered = []
    
    # Filter by paths if provided
    if project_paths:
        paths = [p.strip() for p in project_paths.split(',')]
        path_set = set(paths)
        for project in projects:
            if project.path_with_namespace in path_set:
                filtered.append(project)
        logger.info(f"Filtered to {len(filtered)} project(s) by path: {', '.join(paths)}")
        return filtered
    
    # Filter by IDs if provided
    if project_ids:
        try:
            ids = [int(id_str.strip()) for id_str in project_ids.split(',')]
            id_set = set(ids)
            for project in projects:
                if project.id in id_set:
                    filtered.append(project)
            logger.info(f"Filtered to {len(filtered)} project(s) by ID: {', '.join(map(str, ids))}")
            return filtered
        except ValueError as e:
            logger.error(f"Invalid project IDs format: {e}. Expected comma-separated numbers.")
            raise ValueError(f"Invalid project IDs: {project_ids}. Expected format: '123,456,789'")
    
    return projects


def validate_date_range(after_date: Optional[str], before_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate and convert date range to ISO 8601 format.
    
    Date range is now OPTIONAL for delta discovery since the new paginated
    approach handles large repositories without timeouts.
    
    Args:
        after_date: Start date in YYYY-MM-DD format (optional)
        before_date: End date in YYYY-MM-DD format (optional)
        
    Returns:
        Tuple of (after_date, before_date) as ISO 8601 strings, or (None, None) if not provided
        
    Raises:
        ValueError: If date format is invalid or date order is wrong
    """
    after_date_iso = None
    before_date_iso = None
    
    # Parse after date if provided
    if after_date:
        after_dt = parse_date(after_date)
        after_date_iso = after_dt.strftime("%Y-%m-%dT00:00:00Z")
    
    # Parse before date if provided
    if before_date:
        before_dt = parse_date(before_date)
        before_date_iso = before_dt.strftime("%Y-%m-%dT23:59:59Z")
        
        # If both provided, validate date order
        if after_date:
            if after_dt >= before_dt:
                raise ValueError(
                    f"Invalid date range: --after ({after_dt.date()}) must be before --before ({before_dt.date()})"
                )
    
    return after_date_iso, before_date_iso


def write_results_to_csv(results: List[CommitSearchResult], output_path: str):
    """
    Write search results to a CSV file.

    Args:
        results: List of CommitSearchResult objects
        output_path: Path to output CSV file
    """
    logger = logging.getLogger(__name__)
    
    fieldnames = [
        "commit_sha",
        "project_id",
        "project_name",
        "project_path",
        "project_web_url",
        "commit_web_url",
        "author_name",
        "author_email",
        "title",
        "created_at",
        "branches",
        "tags",
        "found",
        "error",
    ]

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    "commit_sha": result.commit_sha,
                    "project_id": result.project_id,
                    "project_name": result.project_name,
                    "project_path": result.project_path,
                    "project_web_url": result.project_web_url,
                    "commit_web_url": result.commit_web_url,
                    "author_name": result.author_name,
                    "author_email": result.author_email,
                    "title": result.title,
                    "created_at": result.created_at,
                    "branches": result.branches,
                    "tags": result.tags,
                    "found": result.found,
                    "error": result.error,
                })
        
        logger.info(f"Results written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV output: {e}")
        raise


def handle_search_command(args):
    """Handle the search subcommand (original functionality)."""
    logger = logging.getLogger(__name__)
    
    try:
        # Step 1: Load configuration
        logger.info(f"Loading configuration from {args.config}")
        try:
            config = load_config(args.config)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {args.config}")
            logger.error("Please create a config.yaml file. See config.example.yaml for reference.")
            sys.exit(1)
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)

        logger.info(f"  Mode: {config.scan.mode}")
        logger.info(f"  GitLab: {config.gitlab.base_url}")

        # Step 2: Initialize GitLab client
        logger.info("Initializing GitLab API client")
        client = GitLabClient(
            base_url=config.gitlab.base_url,
            private_token=config.gitlab.private_token,
            api_version=config.gitlab.api_version,
            verify_ssl=config.gitlab.verify_ssl,
            timeout_seconds=config.gitlab.timeout_seconds,
        )

        # Test connection
        try:
            logger.info("Testing GitLab connection...")
            client.test_connection()
            logger.info("  Connection successful")
        except GitLabAPIError as e:
            logger.error(f"Failed to connect to GitLab: {e}")
            sys.exit(1)

        # Step 3: Resolve projects to search
        logger.info("Resolving projects to search...")
        try:
            projects = resolve_projects(config, client)
        except GitLabAPIError as e:
            logger.error(f"Failed to resolve projects: {e}")
            sys.exit(1)

        if not projects:
            logger.error("No projects found to search. Check your configuration.")
            sys.exit(1)

        logger.info(f"  Will search across {len(projects)} projects")
        if args.verbose:
            for project in projects[:5]:  # Show first 5 in verbose mode
                logger.debug(f"    - {project.path_with_namespace}")
            if len(projects) > 5:
                logger.debug(f"    ... and {len(projects) - 5} more")

        # Step 4: Load commit SHAs
        logger.info(f"Loading commit SHAs from {args.commits_file}")
        try:
            commit_shas = load_commit_shas_from_file(args.commits_file)
        except FileNotFoundError:
            logger.error(f"Commits file not found: {args.commits_file}")
            sys.exit(1)
        except IOError as e:
            logger.error(f"Failed to read commits file: {e}")
            sys.exit(1)

        if not commit_shas:
            logger.error("No commit SHAs found in input file")
            sys.exit(1)

        logger.info(f"  Loaded {len(commit_shas)} commit SHAs")

        # Step 5: Search for commits
        logger.info("Searching for commits across projects...")
        logger.info("(This may take a while depending on the number of projects and commits)")
        
        finder = CommitFinder(client, projects)
        results = finder.search_commits(commit_shas)

        # Step 6: Write results to CSV
        logger.info(f"Writing results to {args.output}")
        write_results_to_csv(results, args.output)

        # Summary
        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  Total commits searched: {len(commit_shas)}")
        logger.info(f"  Total projects searched: {len(projects)}")
        logger.info(f"  Commit-project matches found: {len(results)}")
        found_commits = len(set(r.commit_sha for r in results if r.found))
        logger.info(f"  Unique commits found: {found_commits}")
        not_found = len(commit_shas) - found_commits
        if not_found > 0:
            logger.warning(f"  Commits not found in any project: {not_found}")
        logger.info(f"  Output written to: {args.output}")
        logger.info("=" * 60)
        logger.info("Done!")

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(1)


def handle_delta_command(args):
    """Handle the delta subcommand (new functionality)."""
    logger = logging.getLogger(__name__)
    
    try:
        # Step 1: Load configuration
        logger.info(f"Loading configuration from {args.config}")
        try:
            config = load_config(args.config)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {args.config}")
            logger.error("Please create a config.yaml file. See config.example.yaml for reference.")
            sys.exit(1)
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)

        logger.info(f"  Mode: {config.scan.mode}")
        logger.info(f"  GitLab: {config.gitlab.base_url}")

        # Step 2: Initialize GitLab client
        logger.info("Initializing GitLab API client")
        client = GitLabClient(
            base_url=config.gitlab.base_url,
            private_token=config.gitlab.private_token,
            api_version=config.gitlab.api_version,
            verify_ssl=config.gitlab.verify_ssl,
            timeout_seconds=config.gitlab.timeout_seconds,
        )

        # Test connection
        try:
            logger.info("Testing GitLab connection...")
            client.test_connection()
            logger.info("  Connection successful")
        except GitLabAPIError as e:
            logger.error(f"Failed to connect to GitLab: {e}")
            sys.exit(1)

        # Step 3: Resolve projects to compare
        logger.info("Resolving projects to compare...")
        try:
            projects = resolve_projects(config, client)
        except GitLabAPIError as e:
            logger.error(f"Failed to resolve projects: {e}")
            sys.exit(1)

        if not projects:
            logger.error("No projects found to compare. Check your configuration.")
            sys.exit(1)

        # Step 3a: Filter or fetch projects if CLI arguments provided
        cli_project_paths = getattr(args, 'projects', None)
        cli_project_ids = getattr(args, 'project_ids', None)
        
        if cli_project_paths or cli_project_ids:
            logger.info("Processing projects based on CLI arguments...")
            
            # If project IDs are specified, try to fetch them directly from GitLab
            # even if they're not in config (allows ad-hoc project selection)
            if cli_project_ids:
                try:
                    ids = [int(id_str.strip()) for id_str in cli_project_ids.split(',')]
                    # Check which IDs are already in the projects list
                    existing_ids = {p.id for p in projects}
                    missing_ids = [pid for pid in ids if pid not in existing_ids]
                    
                    # Fetch missing projects directly from GitLab
                    if missing_ids:
                        logger.info(f"Fetching {len(missing_ids)} project(s) by ID from GitLab...")
                        from .project_resolver import ProjectInfo
                        for project_id in missing_ids:
                            try:
                                project_data = client.get_project_by_id(project_id)
                                project_info = ProjectInfo(
                                    id=project_data['id'],
                                    name=project_data['name'],
                                    path_with_namespace=project_data['path_with_namespace'],
                                    web_url=project_data['web_url']
                                )
                                projects.append(project_info)
                                logger.info(f"  ✓ Fetched project {project_id}: {project_info.path_with_namespace}")
                            except GitLabAPIError as e:
                                logger.warning(f"  ✗ Could not fetch project {project_id}: {e}")
                    
                    # Now filter to only the requested IDs
                    id_set = set(ids)
                    projects = [p for p in projects if p.id in id_set]
                    logger.info(f"Filtered to {len(projects)} project(s) by ID: {', '.join(map(str, ids))}")
                except ValueError as e:
                    logger.error(f"Invalid project IDs format: {e}. Expected comma-separated numbers.")
                    sys.exit(1)
            
            # If project paths are specified, filter from existing projects
            elif cli_project_paths:
                projects = filter_projects_by_cli_args(
                    projects,
                    project_paths=cli_project_paths,
                    project_ids=None
                )
        
        if not projects:
            logger.error("No projects found. Check your --projects or --project-ids arguments.")
            if cli_project_ids:
                logger.error(f"Project ID(s) {cli_project_ids} may not exist or you may not have access.")
            sys.exit(1)

        logger.info(f"  Will compare across {len(projects)} project(s)")
        if args.verbose:
            for project in projects:
                logger.debug(f"    - {project.path_with_namespace} (ID: {project.id})")

        # Step 4: Validate date range (optional for delta discovery)
        after_date_iso = None
        before_date_iso = None
        
        if getattr(args, 'after', None) or getattr(args, 'before', None):
            logger.info("Validating date range...")
            try:
                after_date_iso, before_date_iso = validate_date_range(
                    getattr(args, 'after', None),
                    getattr(args, 'before', None)
                )
                if after_date_iso:
                    logger.info(f"  Filtering commits after: {getattr(args, 'after')}")
                if before_date_iso:
                    logger.info(f"  Filtering commits before: {getattr(args, 'before')}")
            except ValueError as e:
                logger.error(f"Date validation error: {e}")
                logger.error("\nDate range format:")
                logger.error("  --after YYYY-MM-DD (optional, filter commits after this date)")
                logger.error("  --before YYYY-MM-DD (optional, filter commits before this date)")
                logger.error("\nExample:")
                logger.error("  gitdoctor delta --base TAG1 --target TAG2 --after 2025-09-01 --before 2025-11-01")
                sys.exit(1)
        else:
            logger.info("No date filter specified - fetching all commits between refs")

        # Step 5: Find deltas
        logger.info(f"Comparing '{args.base}' to '{args.target}'...")
        logger.info("(This may take a while depending on the number of projects)")
        
        finder = DeltaFinder(client, projects)
        deltas = finder.find_deltas(
            base_ref=args.base,
            target_ref=args.target,
            after_date=after_date_iso,
            before_date=before_date_iso
        )

        # Step 6: Generate summary (needed for HTML export)
        summary = finder.generate_summary(deltas)
        
        # Step 7: Create JIRA linker if configured (config file or command line)
        jira_linker = None
        jira_url = getattr(args, 'jira_url', None) or config.jira.base_url
        jira_project = getattr(args, 'jira_project', None) or config.jira.project_key
        
        if jira_url:
            jira_linker = create_jira_linker(
                jira_base_url=jira_url,
                project_key=jira_project
            )
            if jira_linker:
                logger.info("JIRA integration enabled - extracting ticket references")
                if config.jira.base_url:
                    logger.info(f"  Using JIRA URL from config: {config.jira.base_url}")
                if config.jira.project_key:
                    logger.info(f"  Using JIRA project key from config: {config.jira.project_key}")
        
        # Step 8: Export results
        logger.info(f"Exporting results to {args.output}")
        exporter = get_exporter(args.format)
        
        # HTML exporter needs summary for enhanced reporting
        if args.format == "html":
            exporter.export(deltas, args.output, summary=summary, jira_linker=jira_linker)
        elif args.format == "csv" and jira_linker:
            # CSV exporter supports JIRA linker
            exporter.export(deltas, args.output, jira_linker=jira_linker)
        else:
            exporter.export(deltas, args.output)

        # Step 9: Send notifications if configured (config file or command line)
        slack_webhook = getattr(args, 'slack_webhook', None) or config.notifications.slack_webhook
        if slack_webhook:
            slack_notifier = create_slack_notifier(slack_webhook)
            if slack_notifier:
                logger.info("Sending Slack notification...")
                if config.notifications.slack_webhook:
                    logger.info("  Using Slack webhook from config")
                slack_notifier.send_delta_notification(
                    summary=summary,
                    output_file=args.output,
                    base_ref=args.base,
                    target_ref=args.target
                )
        
        teams_webhook = getattr(args, 'teams_webhook', None) or config.notifications.teams_webhook
        if teams_webhook:
            teams_notifier = create_teams_notifier(teams_webhook)
            if teams_notifier:
                logger.info("Sending Teams notification...")
                if config.notifications.teams_webhook:
                    logger.info("  Using Teams webhook from config")
                teams_notifier.send_delta_notification(
                    summary=summary,
                    output_file=args.output,
                    base_ref=args.base,
                    target_ref=args.target
                )

        # Step 10: Display summary
        print()  # Blank line
        print(summary)
        
        # Step 11: Display JIRA ticket summary if enabled
        if jira_linker:
            ticket_summary = jira_linker.generate_ticket_summary(deltas)
            if ticket_summary:
                print()
                print("=" * 60)
                print("JIRA Tickets Found")
                print("=" * 60)
                for ticket_id, ticket_data in sorted(ticket_summary.items()):
                    print(f"{ticket_id}: {ticket_data['count']} commit(s) in {len(ticket_data['projects'])} project(s)")
                    print(f"  URL: {ticket_data['url']}")
                print("=" * 60)

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="gitdoctor",
        description=(
            "GitDoctor - Map commits and discover deltas across GitLab repositories."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to execute"
    )

    # ===== SEARCH COMMAND (original functionality) =====
    search_parser = subparsers.add_parser(
        "search",
        help="Search for specific commits across repositories",
        description="Search for commit SHAs across configured GitLab projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitdoctor search -i commits.txt -o results.csv
  gitdoctor search -c config.yaml -i commits.txt -o output.csv -v
        """
    )

    search_parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)"
    )

    search_parser.add_argument(
        "-i", "--commits-file",
        required=True,
        help="Path to file containing commit SHAs (one per line)"
    )

    search_parser.add_argument(
        "-o", "--output",
        default="gitlab_commit_mapping.csv",
        help="Path to output CSV file (default: gitlab_commit_mapping.csv)"
    )

    search_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    # ===== DELTA COMMAND (new functionality) =====
    delta_parser = subparsers.add_parser(
        "delta",
        help="Discover delta between two releases/tags/branches",
        description="Compare two references and find all commits between them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two tags - get ALL commits between them
  gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.csv

  # Compare with optional date filter
  gitdoctor delta --base v1.0.0 --target v2.0.0 \\
                  --after 2025-09-01 --before 2025-11-01 \\
                  -o delta.csv

  # Compare specific projects only (overrides config)
  gitdoctor delta --base TAG1 --target TAG2 \\
                  --projects "myorg/backend/user-service,myorg/backend/api" \\
                  -o delta.csv

  # Compare by project IDs
  gitdoctor delta --base TAG1 --target TAG2 \\
                  --project-ids "9795,6050" \\
                  -o delta.csv

  # Use custom config and export as HTML with JIRA
  gitdoctor delta -c config.yaml \\
                  --base TAG1 --target TAG2 \\
                  -o delta.html --format html -v

Note: Uses paginated API - handles large repositories without timeouts.
      Date filters are optional and can be used to narrow down results.
        """
    )

    delta_parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)"
    )

    delta_parser.add_argument(
        "--base",
        required=True,
        help="Base reference (starting tag/branch/commit)"
    )

    delta_parser.add_argument(
        "--target",
        required=True,
        help="Target reference (ending tag/branch/commit)"
    )

    delta_parser.add_argument(
        "-o", "--output",
        default="delta.csv",
        help="Path to output file (default: delta.csv)"
    )

    delta_parser.add_argument(
        "--format",
        choices=["csv", "json", "html"],
        default="csv",
        help="Output format: csv, json, or html (default: csv)"
    )

    delta_parser.add_argument(
        "--after",
        help="Filter commits after this date (optional). Format: YYYY-MM-DD (e.g., 2025-09-01). "
             "If not provided, all commits between refs are included."
    )

    delta_parser.add_argument(
        "--before",
        help="Filter commits before this date (optional). Format: YYYY-MM-DD (e.g., 2025-11-01). "
             "If not provided, all commits between refs are included."
    )

    delta_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    # Project filtering options
    delta_parser.add_argument(
        "--projects",
        help="Comma-separated list of project paths to compare (overrides config). "
             "Example: --projects 'myorg/backend/user-service,myorg/backend/api'"
    )

    delta_parser.add_argument(
        "--project-ids",
        help="Comma-separated list of project IDs to compare (overrides config). "
             "Example: --project-ids '9795,6050'"
    )

    # Notification options
    delta_parser.add_argument(
        "--slack-webhook",
        help="Slack webhook URL to send notification (optional)"
    )

    delta_parser.add_argument(
        "--teams-webhook",
        help="Microsoft Teams webhook URL to send notification (optional)"
    )

    delta_parser.add_argument(
        "--jira-url",
        help="JIRA base URL for ticket linking (e.g., https://jira.company.com). No access token needed - only extracts ticket patterns from commits."
    )

    delta_parser.add_argument(
        "--jira-project",
        help="JIRA project key to filter tickets (e.g., MON). If not specified, extracts all ticket patterns"
    )

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, check for old-style arguments (backward compatibility)
    if not args.command:
        # Check if user is using old syntax (gitdoctor -i commits.txt)
        if len(sys.argv) > 1 and (sys.argv[1] == '-i' or '--commits-file' in sys.argv):
            # Parse as search command for backward compatibility
            sys.argv.insert(1, 'search')
            args = parser.parse_args()
        else:
            parser.print_help()
            sys.exit(0)

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    # Print banner
    logger.info("=" * 60)
    logger.info(f"GitDoctor v{__version__}")
    logger.info("=" * 60)

    # Route to appropriate command handler
    if args.command == "search":
        handle_search_command(args)
    elif args.command == "delta":
        handle_delta_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

