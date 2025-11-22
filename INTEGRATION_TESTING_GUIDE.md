# GitDoctor - Integration Testing Guide

This guide will walk you through testing the tool with your real GitLab instance.

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Access to your GitLab instance (URL)
- [ ] A GitLab Personal Access Token (PAT) with `api`, `read_api`, and `read_repository` scopes
- [ ] Knowledge of at least one GitLab group or project path you want to test with
- [ ] A few commit SHAs you know exist in your repositories
- [ ] The tool installed in a virtual environment

## Step-by-Step Integration Testing

### Step 1: Prepare Your GitLab Personal Access Token

1. Log into your GitLab instance
2. Navigate to: **User Settings → Access Tokens**
3. Create a new token:
   - **Name**: `gitdoctor-test`
   - **Expiration**: Set according to your needs (e.g., 30 days)
   - **Scopes**: Select these three:
     - ☑ `api`
     - ☑ `read_api`
     - ☑ `read_repository`
4. Click **"Create personal access token"**
5. **IMPORTANT**: Copy the token immediately (you won't see it again)
6. Save it securely (password manager recommended)

### Step 2: Identify Your Test Scope

You need to decide what to search. Pick ONE of these approaches:

#### Option A: Test with a Specific Group (Auto-Discover Mode)

Best for: Comprehensive testing across multiple repositories

You need:
- **Group path**: Found in GitLab URL when viewing the group
  - Example: `https://gitlab.company.com/dfs-core/devops` → group path is `dfs-core/devops`

#### Option B: Test with Specific Projects (Explicit Mode)

Best for: Faster, targeted testing

You need:
- **Project paths**: Found in GitLab URL or project settings
  - Example: `https://gitlab.company.com/dfs-core/devops/my-app` → project path is `dfs-core/devops/my-app`
  - Get 2-3 project paths for testing

### Step 3: Get Test Commit SHAs

You need a few commit SHAs that you KNOW exist in your projects.

**Easy way to get them:**

1. Go to one of your projects in GitLab web UI
2. Click **Repository → Commits**
3. Copy 3-5 recent commit SHAs (the long hex strings)
4. Example: `a1b2c3d4e5f6789012345678901234567890abcd`

**Or use git command line:**

```bash
cd /path/to/your/local/repo
git log --oneline -5
# Copy the commit hashes shown
```

### Step 4: Create Your Test Configuration

```bash
cd /path/to/your/project/gitdoctor
cp config.example.yaml config.yaml
```

Open `config.yaml` in your editor and fill in:

#### For Auto-Discover Mode (Option A):

```yaml
gitlab:
  base_url: "YOUR_GITLAB_URL_HERE"  # e.g., https://gitlab.company.com
  private_token: "YOUR_PAT_TOKEN_HERE"
  verify_ssl: true
  timeout_seconds: 15

scan:
  mode: "auto_discover"

groups:
  include_subgroups: true  # Set to false if you only want the main group
  by_path:
    - "YOUR_GROUP_PATH_HERE"  # e.g., dfs-core/devops

# Optional: Add filters to speed up first test
filters:
  exclude_project_paths:
    # - "group/very-large-repo"  # Uncomment and add if needed
```

#### For Explicit Mode (Option B):

```yaml
gitlab:
  base_url: "YOUR_GITLAB_URL_HERE"
  private_token: "YOUR_PAT_TOKEN_HERE"
  verify_ssl: true
  timeout_seconds: 15

scan:
  mode: "explicit"

projects:
  by_path:
    - "YOUR_PROJECT_PATH_1"  # e.g., dfs-core/devops/project1
    - "YOUR_PROJECT_PATH_2"  # e.g., dfs-core/devops/project2
    - "YOUR_PROJECT_PATH_3"  # Add 2-3 projects
```

**IMPORTANT**: Replace all `YOUR_XXX_HERE` placeholders with your actual values!

### Step 5: Create Test Commits File

Create a file called `test-commits.txt` with your commit SHAs:

```bash
cat > test-commits.txt << 'EOF'
a1b2c3d4e5f6789012345678901234567890abcd
b2c3d4e5f6789012345678901234567890abcdef
c3d4e5f6789012345678901234567890abcdef12
EOF
```

Replace those example SHAs with your actual commit SHAs from Step 3.

### Step 6: Test the Connection

First, verify your configuration is correct:

```bash
source venv/bin/activate
gitdoctor --version
```

You should see: `gitdoctor 1.0.0`

### Step 7: Run Your First Test (Verbose Mode)

Run with verbose logging to see detailed output:

```bash
gitdoctor -i test-commits.txt -o test-results.csv -v
```

**What to expect:**

```
============================================================
GitDoctor v1.0.0
============================================================
Loading configuration from config.yaml
  Mode: auto_discover (or explicit)
  GitLab: https://your-gitlab-instance.com
Initializing GitLab API client
Testing GitLab connection...
  Connection successful
Resolving projects to search...
  Will search across X projects
Loading commit SHAs from test-commits.txt
  Loaded Y commit SHAs
Searching for commits across projects...
(This may take a while depending on the number of projects and commits)
[1/Y] Searching for commit abc123...
  Found in 2 project(s)
[2/Y] Searching for commit def456...
  Found in 1 project(s)
...
Writing results to test-results.csv
============================================================
Summary:
  Total commits searched: Y
  Total projects searched: X
  Commit-project matches found: Z
  Unique commits found: W
  Output written to: test-results.csv
============================================================
Done!
```

### Step 8: Verify the Results

Open `test-results.csv` in Excel or a text editor:

**Expected columns:**
- commit_sha
- project_id
- project_name
- project_path
- project_web_url
- commit_web_url
- author_name
- author_email
- title
- created_at
- branches
- tags
- found
- error

**What to check:**

1. **You should see at least one row** for commits that exist in your repositories
2. **`found` column should be TRUE** for known commits
3. **`branches` column should show branch names** like `master|develop|feature-x`
4. **`commit_web_url` should be clickable** and take you to the commit in GitLab
5. **No errors** in the `error` column (should be empty for found commits)

### Step 9: Validate One Result Manually

Pick one row from the CSV and verify it manually:

1. Copy the `commit_web_url` from the CSV
2. Open it in your browser
3. Verify:
   - The commit exists
   - The author matches
   - The title matches
   - The branches shown in GitLab match the CSV

If all matches → **Success!** Your tool is working correctly.

## Troubleshooting Your Integration Test

### Error: "Authentication failed"

**Problem**: Your PAT is incorrect or expired

**Solutions**:
- Verify you copied the entire token (no spaces or line breaks)
- Check the token hasn't expired
- Regenerate the token and update config.yaml
- Ensure the token has the required scopes

### Error: "Access forbidden"

**Problem**: You don't have permission to access the group/project

**Solutions**:
- Verify you have at least "Reporter" or "Guest" access
- Check the group/project path is spelled correctly (case-sensitive)
- Try with a different group/project where you definitely have access
- Ask your GitLab admin to grant you access

### Error: "Resource not found"

**Problem**: The group/project path doesn't exist or you can't access it

**Solutions**:
- Double-check the path in GitLab web UI (copy from URL bar)
- Remove `/` from start and end of paths
- Ensure group/project is not private if you're using a public token
- Try using project ID instead of path

### Error: "SSL verification failed"

**Problem**: Self-signed certificate or corporate proxy

**Solutions**:
- For testing only, set `verify_ssl: false` in config.yaml
- For production, ask IT to help install proper SSL certificates
- Check if you need to configure proxy settings

### No results found but commits definitely exist

**Problem**: Commits exist but not in the searched projects

**Solutions**:
- Verify the commits are in the projects you're searching
- If using explicit mode, make sure you listed the right projects
- If using auto_discover, check that the group contains the projects
- Try verbose mode (`-v`) to see which projects are being searched
- Manually check a commit in GitLab web UI to confirm the project path

### Tool runs very slowly

**Problem**: Too many projects to search

**Solutions**:
- Switch to explicit mode for faster testing
- Add large repositories to `exclude_project_paths`
- Use a smaller group for testing
- Be patient (10 projects × 5 commits = ~5-10 seconds is normal)

## Next Steps After Successful Testing

Once you've confirmed the tool works with your GitLab instance:

### 1. Create Production Configuration

```bash
cp config.yaml config-production.yaml
```

Edit `config-production.yaml` with your production settings and project scope.

### 2. Set Up Multiple Configurations

Create different configs for different use cases:

```bash
# Quick check of critical services
config-quick.yaml

# Full deployment check across all services  
config-comprehensive.yaml

# Production-only repositories
config-production.yaml

# Development/staging repositories
config-staging.yaml
```

### 3. Document Your Setup

Create a team wiki page with:
- Your GitLab base URL
- Which groups/projects to use for different checks
- Common commit SHA sources
- Team-specific troubleshooting tips

### 4. Share with Team

If others will use the tool:
- Share the installation instructions
- Share the CONFLUENCE_HANDBOOK.txt
- Help them create their own PATs
- Set up a shared `config.example.yaml` with your organization's defaults

### 5. Integrate into Workflows

Consider integrating the tool into:
- Release checklists
- Deployment verification procedures
- QA testing workflows
- Compliance audit processes

## Example Real-World Scenarios

### Scenario 1: Verify Hotfix Deployment

```bash
# 1. Get hotfix commit SHA from developer
echo "abc123commit" > hotfix.txt

# 2. Run with production config
gitdoctor -c config-production.yaml -i hotfix.txt -o hotfix-check.csv

# 3. Open hotfix-check.csv and verify commit is in master/main branch
```

### Scenario 2: Track Library Update

```bash
# 1. Get commits from library update PR
cat > library-update.txt << EOF
commit1
commit2
commit3
EOF

# 2. Search across all microservices
gitdoctor -c config-comprehensive.yaml -i library-update.txt -o update-tracking.csv

# 3. Check which services picked up the update
```

### Scenario 3: Release Audit Report

```bash
# 1. Get all commits from release notes
# commits-release-v2.5.txt (provided by release manager)

# 2. Generate full report
gitdoctor -i commits-release-v2.5.txt -o release-v2.5-audit.csv

# 3. Create pivot table in Excel to analyze deployment coverage
```

## Getting Help

If you encounter issues during integration testing:

1. **Run with verbose flag**: `gitdoctor -i test.txt -o out.csv -v`
2. **Check the README.md**: Comprehensive troubleshooting section
3. **Review CONFLUENCE_HANDBOOK.txt**: User-friendly explanations
4. **Contact support**: Include verbose output and config (with token removed!)

## Security Reminder

- ⚠️ **NEVER commit config.yaml with real tokens to git**
- ⚠️ Add `config.yaml` to `.gitignore`
- ⚠️ Only share tokens through secure channels (password managers)
- ⚠️ Rotate tokens regularly (every 30-90 days)
- ⚠️ Revoke tokens when no longer needed

## Success Criteria

You've successfully completed integration testing when:

- ✅ Tool connects to your GitLab instance without errors
- ✅ Projects/groups are discovered correctly
- ✅ Commits are found in expected repositories
- ✅ CSV output contains accurate data verified against GitLab UI
- ✅ Branches and tags are correctly listed for commits
- ✅ No authentication or permission errors
- ✅ Performance is acceptable for your use case
- ✅ You understand how to configure for different scenarios

Congratulations! You're ready to use GitDoctor in production! 🎉

