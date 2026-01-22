# MR Changes - Intelligent Test Selection

## Overview

The `mr-changes` command extracts complete changeset information from a GitLab merge request, providing all the data needed for intelligent test selection. This enables razor-sharp test coverage with no misses and no unnecessary tests.

## Use Case

When deploying code, you need to know:
- **What exactly changed?** (files, commits, diffs)
- **What stories/tickets are included?** (JIRA references)
- **Which tests should run?** (based on changed files and directories)

## Quick Start

### Basic Usage

```bash
# Using project ID and MR IID
gitdoctor mr-changes --project 123 --mr 456 -o mr-changes.json

# Using project path (e.g., from GitLab URL)
gitdoctor mr-changes --project "your-org/product-domains/transaction/shulka" --mr 789 -o changes.json
```

### Extract from Your GitLab URL

If you have a GitLab URL like:
```
http://gitlab.example.com/your-org/product-domains/transaction/shulka/merge_requests/123
```

Extract:
- **Project path**: `your-org/product-domains/transaction/shulka`
- **MR IID**: `123`

Run:
```bash
gitdoctor mr-changes \
  --project "your-org/product-domains/transaction/shulka" \
  --mr 123 \
  -o mr-changes.json
```

Or from a commit URL like:
```
http://gitlab.example.com/your-org/product-domains/transaction/shulka/commit/ed8d4806309d49b8d894078ebaa18183ac93c140
```

First, find which MR contains this commit, then use the command above.

## Output Formats

### 1. Test Selection Format (Recommended)

**Best for**: Test automation frameworks

```bash
gitdoctor mr-changes --project 123 --mr 456 \
  --format test-selection \
  -o test-input.json
```

**Output structure**:
```json
{
  "test_selection": {
    "mr_info": {
      "mr_iid": 456,
      "project_path": "myorg/backend/api",
      "title": "Add user authentication",
      "source_branch": "feature/auth",
      "target_branch": "master"
    },
    "jira_tickets": ["MON-1234", "MON-1235"],
    "changed_source_files": [
      {
        "path": "src/services/auth/UserService.java",
        "type": "modified",
        "extension": ".java"
      }
    ],
    "changed_test_files": [...],
    "changed_directories": ["src/services/auth", "src/controllers"],
    "files_by_extension": {".java": 15, ".xml": 3},
    "statistics": {
      "total_commits": 5,
      "source_files_changed": 12,
      "test_files_changed": 3
    }
  }
}
```

### 2. Test Selection Detailed (with diffs)

**Best for**: Advanced test selection algorithms that analyze code changes

```bash
gitdoctor mr-changes --project 123 --mr 456 \
  --format test-selection-detailed \
  -o detailed-changes.json
```

Includes full unified diffs for each file change.

### 3. Full JSON

**Best for**: Complete data export

```bash
gitdoctor mr-changes --project 123 --mr 456 \
  --format json \
  -o full-data.json
```

### 4. CSV Format

**Best for**: Spreadsheet analysis

```bash
gitdoctor mr-changes --project 123 --mr 456 \
  --format csv \
  -o changes.csv
```

One row per file change with MR metadata.

## JIRA Integration

Extract JIRA tickets from commit messages automatically:

```bash
gitdoctor mr-changes --project 123 --mr 456 \
  --jira-url https://jira.company.com \
  --jira-project MON \
  -o changes.json
```

Or configure in `config.yaml`:
```yaml
jira:
  base_url: https://jira.company.com
  project_key: MON  # Optional: filter by project
```

## Performance Options

### Faster Output (No Diffs)

If you only need file paths and don't need diff content:

```bash
gitdoctor mr-changes --project 123 --mr 456 \
  --no-diffs \
  -o changes.json
```

This is much faster and produces smaller output files.

## Integration with Test Selection

### Example 1: Run Tests for Changed Directories

```bash
# Get MR changes
gitdoctor mr-changes --project 123 --mr 456 -o changes.json

# Parse and run tests (pseudo-code)
changed_dirs=$(jq -r '.test_selection.changed_directories[]' changes.json)
for dir in $changed_dirs; do
  pytest "tests/${dir}"
done
```

### Example 2: Run Tests Tagged with JIRA Tickets

```bash
# Get JIRA tickets from MR
tickets=$(gitdoctor mr-changes --project 123 --mr 456 -o changes.json | \
          jq -r '.test_selection.jira_tickets[]')

# Run tests tagged with these tickets
pytest -m "ticket in ['MON-1234', 'MON-1235']"
```

### Example 3: Map Files to Test Suites

```python
import json

# Load MR changes
with open('changes.json') as f:
    data = json.load(f)

# Map changed files to test suites
test_suites = set()
for file in data['test_selection']['changed_source_files']:
    if 'services/' in file['path']:
        test_suites.add('integration-tests')
    if 'controllers/' in file['path']:
        test_suites.add('api-tests')
    if file['extension'] == '.java':
        test_suites.add('unit-tests')

# Run mapped test suites
for suite in test_suites:
    print(f"Running {suite}...")
```

## Output Data Structure

### Key Fields for Test Selection

- **`changed_source_files`**: Non-test files (actual code changes)
- **`changed_test_files`**: Test files that were modified
- **`changed_directories`**: All directories with changes
- **`files_by_extension`**: Group files by type (.java, .py, etc.)
- **`jira_tickets`**: All JIRA tickets referenced in commits
- **`commits`**: All commits with their messages (for analysis)

### File Change Types

- `modified`: File was changed
- `added`: New file created
- `deleted`: File removed
- `renamed`: File moved/renamed

## Real-World Example

For your use case with:
```
http://gitlab.example.com/your-org/product-domains/transaction/shulka/commit/ed8d4806...
```

1. **Find the MR** that contains this commit:
   - Go to the commit URL in GitLab
   - Click on the MR link (if commit is part of an MR)
   - Note the MR number (e.g., !123)

2. **Extract changeset**:
```bash
gitdoctor mr-changes \
  --project "your-org/product-domains/transaction/shulka" \
  --mr 123 \
  --format test-selection \
  --jira-url http://gitlab.example.com \
  -o deployment-changes.json
```

3. **Analyze the output**:
   - Review `changed_source_files` for affected code
   - Check `jira_tickets` for related stories
   - Use `changed_directories` to map to test suites
   - Filter tests based on file patterns

4. **Run targeted tests**:
   - Execute only tests relevant to changed files
   - Include tests tagged with JIRA tickets
   - No unnecessary tests, no missed coverage

## Command Reference

### Required Arguments

- `--project`: Project ID or path
- `--mr`: Merge request IID (the visible number)

### Optional Arguments

- `-o, --output`: Output file path (default: mr-changes.json)
- `--format`: Output format (default: test-selection)
  - `test-selection`: Compact for test automation
  - `test-selection-detailed`: With full diffs
  - `json`: Full structured data
  - `csv`: Flat spreadsheet format
- `--no-diffs`: Exclude diff content (faster)
- `--jira-url`: JIRA base URL for ticket linking
- `--jira-project`: JIRA project key filter
- `-v, --verbose`: Verbose logging
- `-c, --config`: Config file path (default: config.yaml)

## Tips

1. **Use test-selection format** for most cases - it's optimized for automation
2. **Add --no-diffs** if you only need file paths (much faster)
3. **Configure JIRA in config.yaml** to avoid passing URLs every time
4. **Parse changed_directories** to map to your test suite structure
5. **Use file extensions** to determine which test framework to run
6. **Check is_test_file** to separate test changes from code changes

## Troubleshooting

### Project Not Found
```bash
# Try using project ID instead of path
gitdoctor mr-changes --project 9795 --mr 123 -o changes.json
```

### MR Not Found
```bash
# Verify MR IID (the number in !123)
# Check if MR exists in GitLab
```

### Large MR Timeout
```bash
# Use --no-diffs for faster processing
gitdoctor mr-changes --project 123 --mr 456 --no-diffs -o changes.json
```

## Next Steps

This command provides the **input data** for intelligent test selection. The next step is to build a **test mapping module** that:

1. Loads the MR changes JSON
2. Maps changed files → test suites (using your project's conventions)
3. Filters tests by JIRA tickets (if you tag tests with ticket IDs)
4. Executes only the relevant tests
5. Reports coverage vs changes

GitDoctor gives you the **"what changed"** - you build the **"what to test"** logic for your specific project structure.

