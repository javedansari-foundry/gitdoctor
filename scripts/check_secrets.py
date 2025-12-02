#!/usr/bin/env python3
"""
Secret Scanner for GitDoctor

Scans codebase for potential secrets, tokens, and sensitive information
that should not be committed to version control.

Usage:
    python scripts/check_secrets.py
    python scripts/check_secrets.py --path config.yaml
    python scripts/check_secrets.py --strict  # Exit with error if secrets found
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse


# Patterns to detect secrets
SECRET_PATTERNS = [
    # GitLab PATs
    (r'glpat-[a-zA-Z0-9]{20,}', 'GitLab Personal Access Token'),
    (r'Rwd[a-zA-Z0-9]{15,}', 'Possible GitLab Token'),
    
    # Generic tokens
    (r'private_token:\s*["\']([^"\']{20,})["\']', 'Private Token in config'),
    (r'password:\s*["\']([^"\']{8,})["\']', 'Password in config'),
    (r'secret:\s*["\']([^"\']{8,})["\']', 'Secret in config'),
    
    # API keys
    (r'api[_-]?key["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', 'API Key'),
    (r'access[_-]?token["\']?\s*[:=]\s*["\']([^"\']{20,})["\']', 'Access Token'),
    
    # AWS keys
    (r'AWS_ACCESS_KEY_ID\s*=\s*["\']([^"\']{20,})["\']', 'AWS Access Key'),
    (r'AWS_SECRET_ACCESS_KEY\s*=\s*["\']([^"\']{40,})["\']', 'AWS Secret Key'),
    
    # Database passwords
    (r'db[_-]?password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', 'Database Password'),
    (r'database[_-]?password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', 'Database Password'),
    
    # Long random strings (likely tokens)
    (r'["\'][a-zA-Z0-9+/=]{40,}["\']', 'Long random string (possible token)'),
]

# Safe patterns (known placeholders - these are OK)
SAFE_PATTERNS = [
    r'YOUR_GITLAB_PERSONAL_ACCESS_TOKEN',
    r'YOUR_.*_HERE',
    r'placeholder',
    r'example\.com',
    r'gitlab\.example\.com',
    r'https://jira\.company\.com',
    r'YOUR_SLACK_WEBHOOK_URL',
    r'YOUR_TEAMS_WEBHOOK_URL',
    r'glpat-xxxxxxxxxxxxxxxxxxxx',  # Example placeholder in docs
    r'your-gitlab-personal-access-token',  # Example placeholder
    r'xxxxxxxx',  # Common placeholder pattern
]

# Files to always skip
SKIP_PATTERNS = [
    r'\.git/',
    r'venv/',
    r'__pycache__/',
    r'\.pyc$',
    r'\.pyo$',
    r'\.pyd$',
    r'\.egg-info/',
    r'node_modules/',
    r'\.gitignore',
    r'DEVELOPMENT_RULES\.md',
    r'check_secrets\.py',  # Don't scan this file itself
]

# File extensions to check
CHECK_EXTENSIONS = ['.py', '.yaml', '.yml', '.json', '.md', '.txt', '.sh', '.env']


def is_safe_pattern(text: str) -> bool:
    """Check if text matches safe placeholder patterns."""
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    path_str = str(file_path)
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, path_str):
            return True
    return False


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a file for secrets.
    
    Returns:
        List of (line_number, pattern_name, matched_text) tuples
    """
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            # Skip comments that are clearly placeholders
            if line.strip().startswith('#') and 'YOUR_' in line:
                continue
                
            for pattern, pattern_name in SECRET_PATTERNS:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    matched_text = match.group(0)
                    # Check if it's a safe placeholder
                    if not is_safe_pattern(matched_text):
                        # Extract actual value if it's a key-value pair
                        if ':' in line or '=' in line:
                            # Try to extract the value part
                            value_match = re.search(r'["\']([^"\']+)["\']', line)
                            if value_match:
                                matched_text = value_match.group(1)
                        findings.append((line_num, pattern_name, matched_text))
    except Exception as e:
        print(f"⚠️  Error scanning {file_path}: {e}", file=sys.stderr)
    
    return findings


def scan_directory(directory: Path, exclude_patterns: Optional[List[str]] = None) -> dict:
    """
    Scan directory for secrets.
    
    Returns:
        Dictionary mapping file paths to lists of findings
    """
    all_findings = {}
    exclude_patterns = exclude_patterns or []
    
    for file_path in directory.rglob('*'):
        # Skip if should be ignored
        if should_skip_file(file_path):
            continue
            
        # Skip if matches exclude patterns
        if exclude_patterns:
            path_str = str(file_path)
            if any(re.search(pattern, path_str) for pattern in exclude_patterns):
                continue
        
        # Only check specific file types
        if file_path.suffix not in CHECK_EXTENSIONS and not file_path.is_file():
            continue
            
        if file_path.is_file():
            findings = scan_file(file_path)
            if findings:
                all_findings[str(file_path)] = findings
    
    return all_findings


def main():
    parser = argparse.ArgumentParser(
        description='Scan codebase for secrets and sensitive information'
    )
    parser.add_argument(
        '--path',
        type=str,
        help='Specific file or directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if secrets are found'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Patterns to exclude (regex)'
    )
    
    args = parser.parse_args()
    
    # Determine scan path
    if args.path:
        scan_path = Path(args.path)
        if not scan_path.exists():
            print(f"❌ Error: Path not found: {scan_path}", file=sys.stderr)
            sys.exit(1)
    else:
        scan_path = Path.cwd()
    
    print(f"🔍 Scanning for secrets in: {scan_path}")
    print("=" * 70)
    
    # Perform scan
    if scan_path.is_file():
        findings = scan_file(scan_path)
        all_findings = {str(scan_path): findings} if findings else {}
    else:
        all_findings = scan_directory(scan_path, args.exclude)
    
    # Report findings
    if not all_findings:
        print("✅ No secrets found! Safe to commit.")
        sys.exit(0)
    
    print(f"\n⚠️  Found {sum(len(f) for f in all_findings.values())} potential secret(s) in {len(all_findings)} file(s):\n")
    
    for file_path, findings in sorted(all_findings.items()):
        print(f"\n📄 {file_path}:")
        for line_num, pattern_name, matched_text in findings:
            # Truncate long matches
            display_text = matched_text[:50] + "..." if len(matched_text) > 50 else matched_text
            print(f"   Line {line_num}: {pattern_name}")
            print(f"   Matched: {display_text}")
    
    print("\n" + "=" * 70)
    print("❌ SECRETS DETECTED! Do not commit these files.")
    print("\nActions:")
    print("  1. Remove secrets from tracked files")
    print("  2. Add files with secrets to .gitignore")
    print("  3. Use config.example.yaml with placeholders")
    print("  4. Use environment variables for secrets")
    print("\nSafe patterns (OK to commit):")
    print("  - YOUR_GITLAB_PERSONAL_ACCESS_TOKEN")
    print("  - placeholder values")
    print("  - example.com URLs")
    
    if args.strict:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

