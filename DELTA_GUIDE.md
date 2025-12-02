# GitDoctor Delta Discovery Guide

This guide explains how to use GitDoctor's **delta discovery** feature to find all commits between two releases, tags, or branches across multiple repositories.

## 🎯 What is Delta Discovery?

Delta Discovery automates the manual process of identifying what changed between two releases across your entire microservices architecture. Instead of manually cloning each repository and running `git log BASE..TARGET`, GitDoctor does this automatically for all configured projects.

**Use cases:**
- **Release Management**: See all commits between v1.0.0 and v2.0.0 across all services
- **Change Tracking**: Identify which features made it into a release
- **Audit & Compliance**: Generate comprehensive change reports
- **QA Testing**: Know exactly what needs to be tested in each service

---

## 🚀 Quick Start

### Basic Usage

```bash
# Compare two tags - get ALL commits between them
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv

# With optional date filter
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o delta.csv
```

**✅ No timeout issues:** Uses paginated API with set difference algorithm - handles repositories of any size.

This will:
1. Search all projects configured in `config.yaml`
2. For each project, fetch commits from both refs using paginated API
3. Compute set difference to find commits unique to target
4. Optionally filter commits by date range (if `--after`/`--before` provided)
5. Export everything to `delta.csv`

---

## 📋 Command Reference

### Core Options

```bash
gitdoctor delta --base BASE_REF --target TARGET_REF [OPTIONS]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--base` | Yes | Starting reference (tag/branch/commit) |
| `--target` | Yes | Ending reference (tag/branch/commit) |
| `--after` | No | Filter commits after this date (YYYY-MM-DD). Optional. |
| `--before` | No | Filter commits before this date (YYYY-MM-DD). Optional. |
| `-o, --output` | No | Output file path (default: `delta.csv`) |
| `-c, --config` | No | Config file path (default: `config.yaml`) |
| `-v, --verbose` | No | Enable detailed logging |

### Advanced Options

| Option | Description | Example |
|--------|-------------|---------|
| `--format` | Output format: `csv`, `json`, or `html` | `--format html` |
| `--jira-url` | JIRA base URL for ticket linking | `--jira-url https://jira.company.com` |
| `--jira-project` | JIRA project key filter (e.g., MON) | `--jira-project MON` |
| `--teams-webhook` | Teams webhook URL for notifications | `--teams-webhook https://...` |

### 📅 Date Filtering (Optional)

- **Date range is OPTIONAL** - Use `--after` and/or `--before` to filter results
- **No time limit** - Handles any date range (uses paginated API)
- **Format**: `YYYY-MM-DD` (e.g., `2025-09-01`)
- **Use cases**: Narrow down results to specific time periods

---

## 💡 Usage Examples

### Example 1: Compare Two Release Tags

```bash
# See ALL changes between two production releases
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  -o release-delta.csv \
  -v

# Or with optional date filter to narrow results
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o release-delta.csv \
  -v
```

**Output:**
```
============================================================
GitDoctor v1.0.0
============================================================
Loading configuration from config.yaml
  Mode: explicit
  GitLab: https://gitlab.example.com
Initializing GitLab API client
Testing GitLab connection...
  Connection successful
Resolving projects to compare...
  Will compare across 3 projects
Finding delta from 'release-v1.0.0' to 'release-v2.0.0'...
[1/3] Comparing in myorg/backend/user-service
  ✓ Found 45 commits
[2/3] Comparing in myorg/backend/order-service
  ✓ Found 32 commits
[3/3] Comparing in myorg/frontend/web-app
  ⊘ Base ref 'release-v1.0.0' not found (skipped)

============================================================
Delta Discovery Summary
============================================================
Base Reference:          release-v1.0.0
Target Reference:        release-v2.0.0
Projects Searched:       3
Projects with Changes:   2
Projects without Changes: 0
Projects with Errors:    1

Total Commits Found:     77
Total Files Changed:     245
Unique Authors:          12

Top 5 Projects by Commit Count:
  1. myorg/backend/user-service: 45 commits
  2. myorg/backend/order-service: 32 commits
============================================================
```

### Example 2: Compare Branches

```bash
# Compare release branches (with date range)
gitdoctor delta \
  --base release/v1.0 \
  --target release/v2.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o branch-comparison.csv
```

### Example 3: Specific Month Range

```bash
# Only show commits from September 2025 (1 month range)
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  --after 2025-09-01 \
  --before 2025-10-01 \
  -o september-changes.csv
```

### Example 4: Export as JSON

```bash
# Export in JSON format for programmatic processing
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o delta.json \
  --format json
```

### Example 5: Using Custom Config

```bash
# Use a config file with specific projects
gitdoctor delta \
  -c config-production.yaml \
  --base v1.0.0 \
  --target v2.0.0 \
  --after 2025-09-01 \
  --before 2025-11-01 \
  -o prod-delta.csv
```

### Example 6: Historical 2-Month Range

```bash
# Get commits from any 2-month period in the past
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  --after 2025-01-01 \
  --before 2025-03-01 \
  -o jan-feb-changes.csv
```

---

## 📊 Output Format

### CSV Output

The CSV file contains one row per commit, with these columns:

| Column | Description |
|--------|-------------|
| `project_path` | Full project path (e.g., `myorg/backend/user-service`) |
| `project_name` | Project name |
| `project_id` | GitLab project ID |
| `project_web_url` | URL to the project |
| `base_ref` | BASE reference used |
| `target_ref` | TARGET reference used |
| `base_exists` | Whether BASE ref exists in this project |
| `target_exists` | Whether TARGET ref exists in this project |
| `commit_sha` | Full commit SHA |
| `short_id` | Short commit SHA |
| `title` | Commit message title |
| `message` | Full commit message |
| `author_name` | Commit author name |
| `author_email` | Commit author email |
| `authored_date` | When commit was authored (ISO 8601) |
| `committed_date` | When commit was committed (ISO 8601) |
| `committer_name` | Committer name |
| `committer_email` | Committer email |
| `commit_web_url` | URL to view commit in GitLab |
| `parent_shas` | Parent commit SHAs (pipe-separated) |
| `compare_timeout` | Whether comparison timed out |
| `compare_same_ref` | Whether BASE and TARGET are identical |
| `error` | Error message if any |

### Example CSV Row

```csv
myorg/backend/user-service,user-service,123,https://gitlab.example.com/myorg/backend/user-service,v1.0.0,v2.0.0,true,true,0a0876c1cfa6905acbaf5b07d6b612aad6c45ce3,0a0876c1,PROJ-123|Add user authentication,PROJ-123|Add user authentication feature,John Doe,john.doe@example.com,2025-09-02T17:44:38.000+05:30,2025-09-02T17:44:38.000+05:30,John Doe,john.doe@example.com,https://gitlab.example.com/myorg/backend/user-service/commit/0a0876c1,parent1|parent2,false,false,
```

### JSON Output

JSON format provides a structured representation:

```json
[
  {
    "project": {
      "id": 123,
      "name": "user-service",
      "path": "myorg/backend/user-service",
      "web_url": "https://gitlab.example.com/myorg/backend/user-service"
    },
    "comparison": {
      "base_ref": "v1.0.0",
      "target_ref": "v2.0.0",
      "base_exists": true,
      "target_exists": true,
      "compare_timeout": false,
      "compare_same_ref": false
    },
    "statistics": {
      "total_commits": 45,
      "filtered_commits": 42,
      "files_changed": 120
    },
    "commits": [
      {
        "sha": "0a0876c1cfa6905acbaf5b07d6b612aad6c45ce3",
        "short_id": "0a0876c1",
        "title": "PROJ-123|Add user authentication",
        "author": {
          "name": "John Doe",
          "email": "john.doe@example.com",
          "date": "2025-09-02T17:44:38.000+05:30"
        }
      }
    ]
  }
]
```

---

## ⚙️ Configuration

Delta discovery uses the same configuration as commit search. Make sure your `config.yaml` has projects configured:

### For Explicit Mode (Fastest)

```yaml
scan:
  mode: "explicit"

projects:
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/api-gateway"
    - "myorg/frontend/web-app"
```

### For Auto-Discover Mode

```yaml
scan:
  mode: "auto_discover"

groups:
  by_path:
    - "myorg"
  include_subgroups: true
```

**💡 Tip:** Use explicit mode for faster comparisons when you know which services matter.

---

## 🎭 Understanding References

The `--base` and `--target` arguments accept:

### 1. **Tags** (Most Common)
```bash
--base release-v1.0.0
--target release-v2.0.0
```

### 2. **Branches**
```bash
--base release/v1.0
--target release/v2.0
```

### 3. **Commit SHAs**
```bash
--base abc123def456
--target def456abc123
```

### 4. **Mixed**
```bash
--base v1.0.0               # tag
--target main               # branch
```

**How it works:**
- GitDoctor checks if the reference exists as a tag first
- If not found as tag, checks if it's a branch
- If not found as branch, checks if it's a commit SHA
- If none found, skips that project

---

## 📅 Date Range Requirements

### Why Date Range is Required

**Date range is MANDATORY** for delta discovery to prevent timeouts with large repositories that may have millions of commits.

**Requirements:**
- ✅ **`--after` is REQUIRED** - Start date for the commit range
- ✅ **`--before` is optional** - End date (defaults to today if not provided)
- ✅ **Maximum 2 months** - Date range must be ≤ 62 days
- ✅ **Any 2-month window** - You can specify any period, not just recent dates

### Date Format

Use `YYYY-MM-DD` format:
- ✅ `2025-09-01` - Valid
- ❌ `09/01/2025` - Invalid
- ❌ `2025-9-1` - Invalid (use zero-padded)

### Examples

**Valid ranges:**
```bash
# Exactly 2 months (62 days)
--after 2025-09-01 --before 2025-11-02

# 1 month range
--after 2025-09-01 --before 2025-10-01

# Historical 2-month range
--after 2025-01-01 --before 2025-03-01

# Only start date (uses today as end, must be ≤ 2 months from today)
--after 2025-11-01  # Only if today is ≤ 2 months from Nov 1
```

**Invalid ranges:**
```bash
# ❌ More than 2 months
--after 2025-01-01 --before 2025-06-01  # 151 days - REJECTED

# ❌ No date provided
# Missing --after - REJECTED

# ❌ Invalid date format
--after 09/01/2025  # Wrong format - REJECTED
```

### Handling Large Date Ranges

If you need to analyze a period longer than 2 months, **split it into multiple 2-month chunks**:

```bash
# Month 1-2
gitdoctor delta --base TAG1 --target TAG2 \
  --after 2025-01-01 --before 2025-03-01 \
  -o delta-jan-feb.csv

# Month 3-4
gitdoctor delta --base TAG1 --target TAG2 \
  --after 2025-03-01 --before 2025-05-01 \
  -o delta-mar-apr.csv

# Month 5-6
gitdoctor delta --base TAG1 --target TAG2 \
  --after 2025-05-01 --before 2025-07-01 \
  -o delta-may-jun.csv
```

Then combine the CSV files in Excel or use a script to merge them.

---

## 📈 Performance Considerations

### Comparison Speed

Delta discovery is fast because it uses GitLab's native compare API:

| Projects | Commits | Time |
|----------|---------|------|
| 10 projects | ~500 commits total | 10-15 seconds |
| 25 projects | ~1,200 commits total | 25-30 seconds |
| 50 projects | ~2,500 commits total | 50-60 seconds |

**Factors affecting speed:**
- Number of projects
- Network latency to GitLab
- Number of commits between refs
- GitLab server load

### Tips for Faster Comparisons

1. **Use explicit mode** with only necessary projects
2. **Use date filtering** to reduce result size
3. **Run during off-peak hours** for large comparisons
4. **Consider project-specific configs** for frequent comparisons

---

## 🔍 Analyzing Results

### Using Excel/LibreOffice

1. Open `delta.csv` in Excel
2. Use AutoFilter to analyze:
   - Filter by `project_path` to see changes per service
   - Filter by `author_name` to see who made changes
   - Sort by `committed_date` for chronological view
   - Group by `project_path` to count commits per project

### Using Command Line

```bash
# Count commits per project
cat delta.csv | cut -d',' -f1 | sort | uniq -c | sort -rn

# List unique authors
cat delta.csv | cut -d',' -f14 | sort -u

# Filter by author
grep "John Doe" delta.csv > john-commits.csv

# Count total commits
wc -l delta.csv
```

### Using Python

```python
import pandas as pd

# Load delta results
df = pd.read_csv('delta.csv')

# Commits per project
commits_by_project = df.groupby('project_path').size()
print(commits_by_project.sort_values(ascending=False))

# Commits per author
commits_by_author = df.groupby('author_name').size()
print(commits_by_author.sort_values(ascending=False))

# Timeline analysis
df['committed_date'] = pd.to_datetime(df['committed_date'])
commits_by_date = df.groupby(df['committed_date'].dt.date).size()
```

---

## 🚨 Troubleshooting

### Issue: "Base ref not found in this project"

**Cause:** The BASE tag/branch doesn't exist in that specific project

**Solutions:**
1. Verify the tag name is correct (case-sensitive)
2. Check if the project existed at that release
3. Some projects may use different tagging conventions
4. This is normal - not all projects have all tags

**Note:** Projects where refs don't exist are marked in the CSV with `base_exists=false` or `target_exists=false`

### Issue: "Comparison timed out"

**Cause:** Too many commits between the two refs (GitLab limit)

**Solutions:**
1. Use date filtering: `--after 2025-01-01`
2. Break into smaller ranges: compare v1.0→v1.5, then v1.5→v2.0
3. Contact GitLab admin to increase timeout

### Issue: Slow performance

**Solutions:**
1. Switch to explicit mode with fewer projects
2. Use date filtering to reduce result size
3. Run during off-peak hours
4. Consider running comparisons in batches

### Issue: Empty results

**Possible causes:**
1. BASE and TARGET are the same (compare_same_ref=true)
2. Refs don't exist in any configured projects
3. Project configurations are incorrect

**Debug steps:**
```bash
# Run with verbose logging
gitdoctor delta --base TAG1 --target TAG2 -o delta.csv -v

# Check the summary at the end
# Look for "Projects with Errors" count
```

---

## 📝 Best Practices

### 1. **Naming Conventions**

Use descriptive output filenames:

```bash
# Good naming
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta-v1.0-to-v2.0.csv
gitdoctor delta --base TAG1 --target TAG2 -o delta-$(date +%Y%m%d).csv

# Bad naming
gitdoctor delta --base v1.0.0 --target v2.0.0 -o output.csv
```

### 2. **Document Your Comparisons**

Create a log of comparisons:

```bash
# Add to your release notes
echo "Delta v1.0.0 to v2.0.0: $(date)" >> release-history.txt
gitdoctor delta --base v1.0.0 --target v2.0.0 -o delta-v2.0.csv
```

### 3. **Use Explicit Configs for Different Scenarios**

```bash
# config-backend.yaml - only backend services
# config-frontend.yaml - only frontend services
# config-critical.yaml - only production-critical services

gitdoctor delta -c config-critical.yaml --base v1.0.0 --target v2.0.0 -o critical-delta.csv
```

### 4. **Automate Regular Comparisons**

```bash
#!/bin/bash
# weekly-delta-check.sh
LAST_TAG=$(git describe --tags --abbrev=0)
CURRENT_TAG="HEAD"

gitdoctor delta \
  --base $LAST_TAG \
  --target $CURRENT_TAG \
  -o weekly-delta-$(date +%Y%m%d).csv

# Email results to team
```

---

## 🔄 Integration with Release Process

### Pre-Release Verification

```bash
# Before releasing v2.0, see what's changed
gitdoctor delta \
  --base v1.0-rc \
  --target v2.0-rc \
  -o pre-release-delta.csv

# Review the changes
# Verify all expected features are present
# Identify any unexpected commits
```

### Post-Release Audit

```bash
# After release, generate official change log
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o release-v2.0-changelog.csv

# Archive for compliance
cp release-v2.0-changelog.csv /archive/release-logs/
```

### Hotfix Tracking

```bash
# See what went into a hotfix
gitdoctor delta \
  --base v2.0.0 \
  --target v2.0.1 \
  -o hotfix-v2.0.1.csv
```

---

## 📚 Related Documentation

- **[README.md](README.md)** - Main documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Getting started guide
- **[EXPLICIT_MODE_GUIDE.md](EXPLICIT_MODE_GUIDE.md)** - Fast project searching
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🎯 Summary

**Delta Discovery replaces this manual process:**

```bash
# OLD WAY (manual, error-prone, time-consuming)
cd project1
git fetch --tags
git log release-v1.0.0..release-v2.0.0 > ../changes.txt

cd ../project2
git fetch --tags
git log release-v1.0.0..release-v2.0.0 >> ../changes.txt

# ... repeat for 20+ projects ...
```

**With a single command:**

```bash
# Using GitDoctor (automated, comprehensive, fast)
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  -o delta.csv
```

**Result:** Complete delta across all services in 30 seconds! 🚀

