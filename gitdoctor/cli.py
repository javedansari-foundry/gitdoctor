"""
Command-line interface for GitDoctor.
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import List

from . import __version__
from .config import load_config, ConfigError
from .api_client import GitLabClient, GitLabAPIError
from .project_resolver import resolve_projects
from .commit_finder import CommitFinder, CommitSearchResult, load_commit_shas_from_file


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


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="gitdoctor",
        description=(
            "Map Git commit SHAs to GitLab repositories. "
            "Searches for commits across configured projects/groups and "
            "outputs a CSV with commit metadata, branches, and tags."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default config
  gitdoctor -i commits.txt -o output.csv

  # Use custom config file
  gitdoctor -c my-config.yaml -i commits.txt -o results.csv

  # Verbose output for debugging
  gitdoctor -i commits.txt -o output.csv -v

For more information, see README.md
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)"
    )

    parser.add_argument(
        "-i", "--commits-file",
        required=True,
        help="Path to file containing commit SHAs (one per line)"
    )

    parser.add_argument(
        "-o", "--output",
        default="gitlab_commit_mapping.csv",
        help="Path to output CSV file (default: gitlab_commit_mapping.csv)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Print banner
        logger.info("=" * 60)
        logger.info(f"GitDoctor v{__version__}")
        logger.info("=" * 60)

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


if __name__ == "__main__":
    main()

