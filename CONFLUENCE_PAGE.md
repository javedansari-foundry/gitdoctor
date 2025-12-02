# GitDoctor - Release Delta Discovery & Commit Tracking Tool

> **Version:** 1.0.0  
> **Author:** Platform Engineering Team  
> **Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Quick Start](#quick-start)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Commands Reference](#commands-reference)
7. [Output Formats](#output-formats)
8. [JIRA Integration](#jira-integration)
9. [Use Cases](#use-cases)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)
12. [Support](#support)

---

## Overview

### What is GitDoctor?

GitDoctor is a command-line tool that automates the process of:
- **Finding commits** across multiple GitLab repositories
- **Comparing releases** (delta discovery between tags/branches)
- **Generating reports** in HTML, CSV, and JSON formats

### Why GitDoctor?

| Before GitDoctor | After GitDoctor |
|------------------|-----------------|
| 2-4 hours manual work per release | 60 seconds automated |
| Run `git log` in each repo manually | Single command for all repos |
| Copy-paste results to spreadsheet | Auto-generated CSV/HTML reports |
| Miss repositories or commits | 100% accuracy, no human error |
| No JIRA ticket correlation | Auto-extracts and links tickets |

### Who Should Use It?

- **Release Managers** - Track what's in each release
- **QA Teams** - Know exactly what to test
- **DevOps Engineers** - Verify deployments
- **Developers** - Find where commits landed
- **Auditors** - Generate compliance reports

---

## Key Features

### 1. Delta Discovery
Compare any two references (tags, branches, commits) across all configured repositories.

```bash
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.csv
```

### 2. Commit Search
Search for specific commit SHAs across your entire codebase.

```bash
gitdoctor search -f commits.txt -o results.csv
```

### 3. Interactive HTML Reports
Beautiful, modern reports with:
- 📊 Visual charts (commits by project/author)
- 🔍 Live search and filtering
- 📁 Collapsible sections
- 🌙 Dark mode toggle
- 📥 Export to CSV/JSON from browser

### 4. JIRA Integration
- Auto-extracts ticket IDs from commit messages
- Direct clickable links to JIRA
- Ticket summary with commit counts

### 5. Flexible Output
- **CSV** - For Excel/spreadsheet analysis
- **JSON** - For programmatic processing
- **HTML** - For visual review and sharing

### 6. Notifications (Optional)
- Microsoft Teams webhook
- Slack webhook

---

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/gitdoctor.git
cd gitdoctor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure

Create `config.yaml` (copy from `config.example.yaml`):

```yaml
gitlab:
  base_url: "https://your-gitlab.com"
  private_token: "your-private-token"
  verify_ssl: true

scan:
  mode: "explicit"

projects:
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/order-service"
    - "myorg/frontend/web-app"
```

### 3. Run

```bash
# Compare two releases
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.html --format html

# Open the report
open delta.html  # or double-click the file
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- GitLab access token with `read_api` scope
- Network access to your GitLab instance

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone https://github.com/your-org/gitdoctor.git
cd gitdoctor

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install GitDoctor
pip install -e .

# 5. Verify installation
gitdoctor --help
```

### Getting a GitLab Token

1. Go to GitLab → **Settings** → **Access Tokens**
2. Create a new token with:
   - **Name:** `gitdoctor`
   - **Scopes:** `read_api`
   - **Expiration:** Set as per your policy
3. Copy the token (you won't see it again!)

---

## Configuration

### Configuration File Location

GitDoctor looks for `config.yaml` in the current directory by default. You can specify a different location:

```bash
gitdoctor delta -c /path/to/config.yaml --base v1.0 --target v2.0
```

### Minimal Configuration

```yaml
gitlab:
  base_url: "https://your-gitlab.com"
  private_token: "glpat-xxxxxxxxxxxx"

scan:
  mode: "explicit"

projects:
  by_path:
    - "group/project1"
    - "group/project2"
```

### Full Configuration Reference

```yaml
# GitLab Connection
gitlab:
  base_url: "https://your-gitlab.com"      # Required
  private_token: "glpat-xxxxxxxxxxxx"      # Required
  verify_ssl: true                          # Optional, default: true
  timeout_seconds: 30                       # Optional, default: 30

# Scan Mode
scan:
  mode: "explicit"  # Options: "explicit" or "auto_discover"

# For Explicit Mode - List specific projects
projects:
  by_id:
    - 123
    - 456
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/order-service"

# For Auto-Discover Mode - Scan GitLab groups
groups:
  by_id:
    - 42
  by_path:
    - "myorg/backend"
  include_subgroups: true

# Optional Filters
filters:
  include_patterns:
    - ".*-service$"       # Regex patterns
  exclude_patterns:
    - ".*-archived$"
  exclude_project_ids:
    - 999
  exclude_project_paths:
    - "myorg/old-project"

# Optional JIRA Integration
jira:
  base_url: "https://your-jira.atlassian.net"
  project_key: "PROJ"  # Extract PROJ-* tickets

# Optional Notifications
notifications:
  teams_webhook: "https://outlook.office.com/webhook/..."
  slack_webhook: "https://hooks.slack.com/services/..."
```

### Scan Modes Explained

#### Explicit Mode (Recommended)
List the exact projects you want to scan:

```yaml
scan:
  mode: "explicit"

projects:
  by_path:
    - "myorg/service-a"
    - "myorg/service-b"
```

**Pros:** Fast, predictable, no surprises  
**Cons:** Must manually add new projects

#### Auto-Discover Mode
Automatically discover all projects in GitLab groups:

```yaml
scan:
  mode: "auto_discover"

groups:
  by_path:
    - "myorg"
  include_subgroups: true
```

**Pros:** Automatically includes new projects  
**Cons:** May include unwanted projects, slower

---

## Commands Reference

### Delta Command (Release Comparison)

```bash
gitdoctor delta [OPTIONS]
```

| Option | Required | Description | Example |
|--------|----------|-------------|---------|
| `--base` | Yes | Base reference (tag/branch/SHA) | `--base v1.0.0` |
| `--target` | Yes | Target reference (tag/branch/SHA) | `--target v2.0.0` |
| `--after` | No | Filter commits after date (YYYY-MM-DD) | `--after 2025-01-01` |
| `--before` | No | Filter commits before date | `--before 2025-12-31` |
| `--projects` | No | Override config with specific projects | `--projects "proj1,proj2"` |
| `--project-ids` | No | Override config with project IDs | `--project-ids "123,456"` |
| `-o, --output` | No | Output file path (default: delta.csv) | `-o report.html` |
| `--format` | No | Output format: csv, json, html | `--format html` |
| `-c, --config` | No | Config file path | `-c prod-config.yaml` |
| `-v, --verbose` | No | Enable detailed logging | `-v` |
| `--jira-url` | No | JIRA base URL (overrides config) | `--jira-url https://jira.com` |
| `--jira-project` | No | JIRA project key | `--jira-project PROJ` |

#### Examples

```bash
# Basic comparison
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.csv

# HTML report with JIRA
gitdoctor delta --base v1.0.0 --target v2.0.0 -o report.html --format html

# Specific projects only
gitdoctor delta --base v1.0.0 --target v2.0.0 \
  --projects "myorg/service-a,myorg/service-b" \
  -o delta.csv

# With date filter
gitdoctor delta --base release-branch --target main \
  --after 2025-09-01 --before 2025-11-30 \
  -o q4-changes.csv

# Verbose mode for debugging
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta.csv -v
```

### Search Command (Find Commits)

```bash
gitdoctor search [OPTIONS]
```

| Option | Required | Description | Example |
|--------|----------|-------------|---------|
| `-f, --file` | No* | File containing commit SHAs | `-f commits.txt` |
| `-s, --sha` | No* | Single commit SHA | `-s abc123def` |
| `-o, --output` | No | Output file path | `-o results.csv` |
| `-c, --config` | No | Config file path | `-c config.yaml` |
| `-v, --verbose` | No | Enable detailed logging | `-v` |

*Either `--file` or `--sha` is required

#### Examples

```bash
# Search from file
gitdoctor search -f commits.txt -o results.csv

# Search single commit
gitdoctor search -s abc123def456 -o result.csv
```

#### Commits File Format

Create a text file with one commit SHA per line:

```
abc123def456789
def456abc123789
789xyz123abc456
```

---

## Output Formats

### CSV Format

Best for: Excel analysis, importing into other tools

```csv
project_path,project_name,commit_sha,title,author_name,committed_date,jira_tickets
myorg/service-a,service-a,abc123,Add feature X,John Doe,2025-09-15,PROJ-123
myorg/service-b,service-b,def456,Fix bug Y,Jane Smith,2025-09-16,PROJ-124|PROJ-125
```

**Columns include:**
- Project information (path, name, ID, URL)
- Commit details (SHA, title, message, date)
- Author information (name, email)
- JIRA tickets (extracted from commit message)

### JSON Format

Best for: Programmatic processing, APIs

```json
[
  {
    "project": {
      "id": 123,
      "name": "service-a",
      "path": "myorg/service-a"
    },
    "commits": [
      {
        "sha": "abc123",
        "title": "Add feature X",
        "author": {"name": "John Doe"}
      }
    ]
  }
]
```

### HTML Format

Best for: Visual review, sharing with stakeholders, presentations

Features:
- **Summary cards** - Total commits, projects, authors, JIRA tickets
- **Tabbed views** - Overview, By Project, By Author, Timeline, JIRA
- **Visual charts** - Bar charts for commits by project/author
- **Live search** - Filter by SHA, message, author
- **Project filter** - Dropdown to filter by project
- **Collapsible sections** - Expand/collapse project details
- **Dark mode** - Toggle for eye comfort
- **In-browser export** - Download CSV/JSON from the report
- **Print-friendly** - Optimized print stylesheet

---

## JIRA Integration

### Enabling JIRA Integration

Add to your `config.yaml`:

```yaml
jira:
  base_url: "https://your-company.atlassian.net"
  project_key: "PROJ"  # Optional - filter to specific project
```

Or use command-line options:

```bash
gitdoctor delta --base v1.0 --target v2.0 \
  --jira-url "https://your-company.atlassian.net" \
  --jira-project "PROJ" \
  -o report.html --format html
```

### How It Works

1. GitDoctor scans commit messages for patterns like:
   - `PROJ-123`
   - `[PROJ-456]`
   - `PROJ-789: Fix bug`

2. Extracted tickets are:
   - Listed in CSV/JSON output
   - Linked in HTML reports
   - Summarized with commit counts

### Example Output

In HTML report, you'll see:
- Ticket badges on each commit
- Dedicated "JIRA Tickets" tab
- Click any ticket to open in JIRA

---

## Use Cases

### 1. Release Comparison

**Scenario:** QA needs to know what changed between v1.0 and v2.0

```bash
gitdoctor delta --base v1.0.0 --target v2.0.0 \
  -o release-v2.0-changes.html --format html
```

### 2. Sprint Review

**Scenario:** Show all commits from the last sprint

```bash
gitdoctor delta --base main --target develop \
  --after 2025-11-01 --before 2025-11-15 \
  -o sprint-23-commits.csv
```

### 3. Hotfix Tracking

**Scenario:** What went into the hotfix release?

```bash
gitdoctor delta --base v2.0.0 --target v2.0.1 \
  -o hotfix-changes.csv
```

### 4. Deployment Verification

**Scenario:** Verify specific commits reached production

```bash
# Create commits.txt with SHAs from JIRA tickets
gitdoctor search -f commits.txt -o deployment-check.csv
```

### 5. Compliance Audit

**Scenario:** Generate change log for audit

```bash
gitdoctor delta --base v1.0.0 --target v2.0.0 \
  -o audit-report.html --format html
# Archive the HTML report for compliance records
```

### 6. Single Repository Check

**Scenario:** Quick check of one specific repo

```bash
gitdoctor delta --base v1.0.0 --target v2.0.0 \
  --projects "myorg/critical-service" \
  -o single-repo-check.csv
```

---

## Troubleshooting

### Common Issues

#### 1. "Configuration file not found"

**Cause:** GitDoctor can't find `config.yaml`

**Solution:**
```bash
# Check current directory
ls config.yaml

# Or specify path explicitly
gitdoctor delta -c /path/to/config.yaml --base v1.0 --target v2.0
```

#### 2. "401 Unauthorized"

**Cause:** Invalid or expired GitLab token

**Solution:**
1. Generate a new token in GitLab → Settings → Access Tokens
2. Ensure token has `read_api` scope
3. Update `config.yaml` with new token

#### 3. "404 Project not found"

**Cause:** Project path is incorrect or you don't have access

**Solution:**
```bash
# Verify project path in GitLab URL
# https://gitlab.com/myorg/backend/service-a
# Project path is: myorg/backend/service-a

# Check your access
curl -H "PRIVATE-TOKEN: your-token" \
  "https://gitlab.com/api/v4/projects/myorg%2Fbackend%2Fservice-a"
```

#### 4. "Base ref not found"

**Cause:** The tag/branch doesn't exist in that repository

**Solution:**
- This is normal - not all repos have all tags
- Check the CSV for `base_exists=false` entries
- These projects are skipped (not an error)

#### 5. "0 commits found" when expecting results

**Cause:** Direction might be swapped

**Solution:**
```bash
# --base is the OLDER reference
# --target is the NEWER reference
# Shows commits in TARGET that are NOT in BASE

# If you swap them, you get the opposite result
gitdoctor delta --base v2.0.0 --target v1.0.0  # Wrong - shows what's in v1 not in v2
gitdoctor delta --base v1.0.0 --target v2.0.0  # Correct - shows what's NEW in v2
```

#### 6. SSL Certificate Error

**Cause:** Self-signed certificate on GitLab

**Solution:**
```yaml
# In config.yaml
gitlab:
  verify_ssl: false  # Use only if necessary
```

#### 7. Timeout Errors

**Cause:** Slow network or large repositories

**Solution:**
```yaml
# In config.yaml
gitlab:
  timeout_seconds: 60  # Increase timeout
```

### Debug Mode

Run with `-v` for detailed logging:

```bash
gitdoctor delta --base v1.0 --target v2.0 -o delta.csv -v
```

This shows:
- API calls being made
- Projects being scanned
- Commit counts per project
- Any errors encountered

---

## FAQ

### Q: How long does it take to run?

**A:** Depends on the number of projects and commits:
- 10 projects, ~500 commits: 10-15 seconds
- 30 projects, ~1500 commits: 30-45 seconds
- 50 projects, ~3000 commits: 60-90 seconds

### Q: Can I compare branches instead of tags?

**A:** Yes! Any git reference works:
```bash
gitdoctor delta --base main --target feature-branch -o delta.csv
```

### Q: Does it work with GitHub?

**A:** Currently GitDoctor is designed for GitLab. GitHub support may be added in future versions.

### Q: Can I schedule it to run automatically?

**A:** Yes! You can run GitDoctor in CI/CD pipelines or cron jobs:
```bash
# Example cron job (daily at 9 AM)
0 9 * * * cd /path/to/gitdoctor && ./venv/bin/gitdoctor delta --base v1.0 --target HEAD -o /reports/daily.csv
```

### Q: How do I add a new repository?

**A:** Add it to your `config.yaml`:
```yaml
projects:
  by_path:
    - "existing/project"
    - "new/project"  # Add new project here
```

### Q: Can I exclude certain repositories?

**A:** Yes, use filters:
```yaml
filters:
  exclude_project_paths:
    - "myorg/archived-project"
    - "myorg/test-project"
```

### Q: The HTML report is too large, how do I reduce it?

**A:** Use date filters or specific projects:
```bash
# Filter by date
gitdoctor delta --base v1.0 --target v2.0 \
  --after 2025-10-01 -o delta.html --format html

# Or specific projects only
gitdoctor delta --base v1.0 --target v2.0 \
  --projects "critical-service-1,critical-service-2" \
  -o delta.html --format html
```

---

## Support

### Getting Help

1. **Check this documentation** - Most questions are answered here
2. **Check the README** - In the GitDoctor repository
3. **Run with `-v`** - Verbose mode helps debug issues
4. **Contact the team** - [Your contact info]

### Reporting Issues

When reporting issues, please include:
1. Command you ran
2. Error message (full output with `-v`)
3. Your Python version (`python --version`)
4. Your OS (macOS, Linux, Windows)

### Contributing

Contributions are welcome! See the repository README for guidelines.

---

## Additional Resources

| Resource | Description | Location |
|----------|-------------|----------|
| README.md | Overview and quick start | Repository root |
| DELTA_GUIDE.md | Detailed delta command guide | Repository root |
| config.example.yaml | Sample configuration | Repository root |
| QUICKSTART.md | 5-minute getting started | Repository root |
| TROUBLESHOOTING.md | Extended troubleshooting | Repository root |

---

*Last updated: December 2025*

