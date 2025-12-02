# Integration Testing Guide for GitDoctor

This guide shows how to test GitDoctor with your GitLab instance.

## ✅ What's Already Configured

I've created the following files for you:

1. **config.yaml** - Example configuration for your GitLab instance
   - URL: `https://gitlab.example.com`
   - Mode: Auto-discover
   - Group: `your-group` (including all subgroups)
   - Excludes: automation repos
   - SSL verification: disabled (for self-signed certificates)

2. **commits.txt** - Contains your 4 test commits:
   - `0a0876c1cfa6905acbaf5b07d6b612aad6c45ce3`
   - `10c9b21f31f3c6ef41799a08a22f564248ca98c3`
   - `75fe7c83205f1161f49bf0d69912d0c918e5d283`
   - `619d2f8bc7ad089295a8553e2b79f7ccf912b7c4`

3. **.gitignore** - Protects your token from being committed

## 🔑 Step 1: Get Your GitLab Personal Access Token

**CRITICAL**: You must have a valid GitLab token to proceed.

### How to Generate Your Token:

1. Open your browser and go to: **https://gitlab.example.com/-/profile/personal_access_tokens**

2. Fill in the form:
   - **Token name**: `gitdoctor`
   - **Expiration date**: Choose based on your policy (suggest 90 days)
   - **Select scopes** - Check these THREE boxes:
     - ☑️ `api`
     - ☑️ `read_api`
     - ☑️ `read_repository`

3. Click **"Create personal access token"**

4. **IMMEDIATELY COPY THE TOKEN** - it will look something like:
   ```
   glpat-xxxxxxxxxxxxxxxxxxxx
   ```
   ⚠️ You won't see it again after you leave the page!

5. Save it securely (password manager recommended)

## 📝 Step 2: Add Your Token to Configuration

Open the `config.yaml` file and replace the placeholder:

```bash
# Open in your editor
nano config.yaml
# or
code config.yaml
# or
vim config.yaml
```

Find this line:
```yaml
private_token: "YOUR_GITLAB_PERSONAL_ACCESS_TOKEN_HERE"
```

Replace it with your actual token:
```yaml
private_token: "glpat-xxxxxxxxxxxxxxxxxxxx"
```

**Save and close the file.**

⚠️ **IMPORTANT**: Never commit this file to git! It's already in .gitignore.

### ⚠️ Common Configuration Mistake - YAML Syntax

Make sure your config.yaml uses proper YAML list syntax:

```yaml
# ✅ CORRECT - Use dashes:
projects:
  by_path:
    - "myorg/backend/user-service"
    - "myorg/backend/order-service"

# ❌ WRONG - Don't use commas:
projects:
  by_path:
    "myorg/backend/user-service",
    "myorg/backend/order-service"
```

If you see error "explicit mode requires at least one project", check for this syntax error!

## 🚀 Step 3: Run Your First Test

Now let's test the tool with your real GitLab!

### 3a. Ensure Virtual Environment is Active

```bash
cd /path/to/your/project/gitdoctor
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### 3b. Verify Installation

```bash
gitdoctor --version
```

Expected output: `gitdoctor 1.0.0`

### 3c. Run the Test with Verbose Output

```bash
gitdoctor -i commits.txt -o results.csv -v
```

## 📊 Step 4: What to Expect

### Expected Process:

```
============================================================
GitDoctor v1.0.0
============================================================
Loading configuration from config.yaml
  Mode: auto_discover
  GitLab: https://gitlab.example.com
Initializing GitLab API client
Testing GitLab connection...
  Connection successful ✓
Resolving projects to search...
  Fetching projects from group path 'your-group' (include_subgroups=True)
  Found XX projects in group 'your-group'
  Applied exclude filter: excluded N projects
  Will search across XX projects
Loading commit SHAs from commits.txt
  Loaded 4 commit SHAs
Searching for commits across projects...
[1/4] Searching for commit 0a0876c1cfa6905acbaf5b07d6b612aad6c45ce3
  Found in X project(s)
[2/4] Searching for commit 10c9b21f31f3c6ef41799a08a22f564248ca98c3
  Found in X project(s)
[3/4] Searching for commit 75fe7c83205f1161f49bf0d69912d0c918e5d283
  Found in X project(s)
[4/4] Searching for commit 619d2f8bc7ad089295a8553e2b79f7ccf912b7c4
  Found in X project(s)
Writing results to results.csv
============================================================
Summary:
  Total commits searched: 4
  Total projects searched: XX
  Commit-project matches found: XX
  Unique commits found: X
  Commits not found in any project: X
  Output written to: results.csv
============================================================
Done!
```

### Timing Expectations:

The first run will be slower because it needs to discover all projects:

- **Project discovery**: 10-30 seconds (depending on group size)
- **Per commit search**: ~100-200ms per project
- **Total time estimate**: 
  - If you have 50 projects: ~20-40 seconds
  - If you have 100 projects: ~40-80 seconds
  - If you have 200 projects: ~80-160 seconds

## ✅ Step 5: Verify the Results

### 5a. Check the CSV File

```bash
# Quick preview in terminal
head -20 results.csv

# Or open in your spreadsheet application
open results.csv  # Mac
# xdg-open results.csv  # Linux
# start results.csv  # Windows
```

### 5b. What to Look For

The CSV should contain these columns:
- `commit_sha` - Your commit hashes
- `project_name` - Repository name
- `project_path` - Full path (e.g., `your-group/devops/my-app`)
- `author_name` - Who made the commit
- `title` - Commit message
- `created_at` - When it was created
- `branches` - All branches containing this commit (pipe-separated)
- `tags` - All tags containing this commit
- `found` - TRUE if found
- `error` - Any errors (should be empty)

### 5c. Manual Verification

Pick one result and verify manually:

1. Find a row where `found` = TRUE
2. Copy the `commit_web_url` value
3. Open it in your browser
4. Verify:
   - The commit exists
   - Author matches
   - Title matches
   - Branches shown in GitLab match the CSV

If everything matches → **Success!** 🎉

## 🔧 Troubleshooting Common Issues

### Issue 1: "Authentication failed"

**Cause**: Token is wrong or expired

**Fix**:
```bash
# 1. Verify you copied the entire token (no spaces)
# 2. Check it hasn't expired
# 3. Regenerate token and update config.yaml
# 4. Make sure token has api, read_api, read_repository scopes
```

### Issue 2: "Group with path 'your-group' not found"

**Cause**: Wrong group path or no access

**Fix**:
```bash
# 1. Verify group path in browser: https://gitlab.example.com/your-group
# 2. Check you have access to view the group
# 3. Try logging in to GitLab web UI with your account
# 4. If group path is different, update config.yaml
```

### Issue 3: SSL/Certificate Errors (even with verify_ssl: false)

**Cause**: Network/proxy issues

**Fix**:
```bash
# Try setting these environment variables:
export PYTHONHTTPSVERIFY=0
export REQUESTS_CA_BUNDLE=""
export CURL_CA_BUNDLE=""

# Then run the tool again
gitdoctor -i commits.txt -o results.csv -v
```

### Issue 4: "Connection timeout" or very slow

**Cause**: Network latency or GitLab server load

**Fix**:
```yaml
# Edit config.yaml and increase timeout:
gitlab:
  timeout_seconds: 30  # or 60
```

### Issue 5: Too many projects discovered (very slow)

**Cause**: your-group has many subgroups

**Fix**:
```yaml
# Option A: Exclude more projects
filters:
  exclude_project_paths:
    - "your-group/automation"
    - "your-group/archived/*"  # Won't work - add specific paths
    - "your-group/legacy/old-project"

# Option B: Search specific subgroup instead
groups:
  by_path:
    - "your-group/devops"  # More specific

# Option C: Switch to explicit mode for faster testing
scan:
  mode: "explicit"
projects:
  by_path:
    - "your-group/devops/project1"
    - "your-group/devops/project2"
```

### Issue 6: Commits not found but they definitely exist

**Possible causes**:
1. Commits are in projects outside your-group group
2. Commits are in excluded automation repos
3. You don't have access to those projects
4. Commits were in branches that have been deleted

**Debug**:
```bash
# Run with verbose to see which projects are searched
gitdoctor -i commits.txt -o results.csv -v

# Look for the project list in output
# Verify your commit's project is in that list
```

## 📈 Next Steps After Successful Test

### 1. Fine-Tune Exclusions

After seeing which projects are discovered, you might want to exclude more:

```yaml
filters:
  exclude_project_paths:
    - "your-group/automation"
    - "your-group/devops/automation"
    - "your-group/test-automation"
    - "your-group/archived/old-monorepo"
    - "your-group/vendor/large-dependency"
```

### 2. Create Different Configurations

Create specialized configs for different scenarios:

```bash
# Quick production check
cp config.yaml config-production.yaml
# Edit to only include production projects

# Development/staging check
cp config.yaml config-staging.yaml
# Edit to only include staging projects

# Quick check of core services
cp config.yaml config-core.yaml
# Use explicit mode with just 5-10 critical projects
```

### 3. Add to Your Workflow

Example workflows:

**Verify hotfix deployment:**
```bash
echo "abc123hotfixcommit" > hotfix.txt
gitdoctor -i hotfix.txt -o hotfix-check.csv
# Check if it's in master/main branch
```

**Track feature across microservices:**
```bash
# Get commits from feature branch
cat > feature-commits.txt
gitdoctor -i feature-commits.txt -o feature-tracking.csv
```

**Release audit:**
```bash
# Get all commits for release v2.5
gitdoctor -i release-v2.5-commits.txt -o release-audit.csv
```

### 4. Share with Your Team

If others need to use this:
1. Share installation instructions (README.md)
2. Share the handbook (CONFLUENCE_HANDBOOK.txt)
3. Help them generate their own PATs
4. Share your refined config.example.yaml (without token)

## 🎓 Understanding Your Configuration

### What Each Setting Does:

```yaml
# Your GitLab URL
base_url: "https://gitlab.example.com"

# Auto-discover mode = search all projects in group
scan:
  mode: "auto_discover"

# The group to search (your-group and all subgroups)
groups:
  include_subgroups: true
  by_path:
    - "your-group"

# Projects to skip (automation repos)
filters:
  exclude_project_paths:
    - "your-group/automation"
    - "your-group/devops/automation"
```

### How It Works:

1. **Discovery Phase**: Tool fetches all projects under `your-group` group
2. **Filtering Phase**: Removes projects matching exclude patterns
3. **Search Phase**: For each commit, searches each remaining project
4. **Metadata Phase**: For found commits, fetches branches and tags
5. **Output Phase**: Writes all results to CSV

## 📞 Getting Help

If you encounter issues:

1. **Run with verbose**: Always use `-v` flag for detailed output
2. **Check logs**: Look for specific error messages
3. **Verify manually**: Check one commit in GitLab web UI
4. **Review docs**:
   - **TROUBLESHOOTING.md** - Complete troubleshooting guide ⭐
   - README.md - Technical reference
   - CONFLUENCE_HANDBOOK.txt - User guide
   - INTEGRATION_TESTING_GUIDE.md - Detailed troubleshooting

## 🔒 Security Reminders

- ✅ config.yaml is in .gitignore
- ✅ Never share your token
- ✅ Rotate tokens every 30-90 days
- ✅ Use minimal required scopes (read-only)
- ✅ Revoke tokens when done

## ✨ Success Checklist

- [ ] Generated GitLab Personal Access Token
- [ ] Updated config.yaml with token
- [ ] Activated virtual environment
- [ ] Ran test successfully
- [ ] CSV contains expected results
- [ ] Manually verified at least one result
- [ ] Understood the output format
- [ ] Knows how to adjust configuration

---

**You're all set!** Run the command and let me know if you encounter any issues. I'm here to help! 🚀

```bash
# THE COMMAND TO RUN:
gitdoctor -i commits.txt -o results.csv -v
```

