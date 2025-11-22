# GitDoctor Troubleshooting Guide

This guide covers common issues you might encounter when setting up and using GitDoctor.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Connection & Authentication](#connection--authentication)
- [Runtime Errors](#runtime-errors)
- [Performance Issues](#performance-issues)

---

## Installation Issues

### ❌ Error: "Cannot declare ('project', 'optional-dependencies') twice"

**What it means:** The `pyproject.toml` file has a duplicate section

**Error message:**
```
tomllib.TOMLDecodeError: Cannot declare ('project', 'optional-dependencies') twice (at line 53, column 31)
```

**Solution:**
The pyproject.toml has been fixed. If you still see this error:

1. Check `pyproject.toml` for duplicate `[project.optional-dependencies]` sections
2. Remove the duplicate (should only appear once)
3. Try installing again: `pip install -e .`

---

### ❌ Command not found: 'gitdoctor'

**What it means:** The package isn't installed or virtual environment isn't activated

**Solutions:**

```bash
# Step 1: Activate virtual environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Step 2: Install package in editable mode
pip install -e .

# Step 3: Verify
gitdoctor --version  # Should show: gitdoctor 1.0.0
which gitdoctor      # Should show path in venv/bin/
```

**Why use `pip install -e .`?**
- The `-e` flag installs in "editable" mode
- This creates the `gitdoctor` command in your PATH
- Changes to source code take effect immediately (no reinstall needed)

---

### ❌ Python version error

**Error message:**
```
Requires-Python: >=3.10
```

**Solution:**
```bash
# Check your Python version
python3 --version

# Must be 3.10 or higher
# If not, install Python 3.10+ and recreate virtual environment
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Configuration Issues

### ❌ Error: "In explicit mode, at least one project must be configured"

**What it means:** Your YAML configuration has incorrect list syntax

**Common cause:** Using commas instead of dashes in YAML lists

**Error in config.yaml:**
```yaml
# ❌ WRONG - Don't use commas
projects:
  by_path:
    "dfs-core/project1",
    "dfs-core/project2",
    "dfs-core/project3"
```

**Fix:**
```yaml
# ✅ CORRECT - Use dashes (-)
projects:
  by_path:
    - "dfs-core/project1"
    - "dfs-core/project2"
    - "dfs-core/project3"
```

**Why?** YAML requires a dash (`-`) prefix for each list item. Commas are NOT valid YAML list syntax.

---

### ❌ Error: "In auto_discover mode, at least one group must be configured"

**What it means:** Groups section is empty or has syntax errors

**Check your config.yaml:**

```yaml
# ❌ WRONG - Empty or wrong syntax
groups:
  by_path:

# ✅ CORRECT
groups:
  by_path:
    - "your-group-name"
  by_id: []  # Can be empty if not using IDs
```

---

### ❌ YAML parsing errors

**Error messages like:**
- "mapping values are not allowed here"
- "could not find expected ':'"
- "found character '\\t' that cannot start any token"

**Common causes:**
1. **Using tabs instead of spaces**
   ```yaml
   # ❌ WRONG - tabs
   gitlab:
   	base_url: "https://..."  # <-- tab character
   
   # ✅ CORRECT - spaces
   gitlab:
     base_url: "https://..."  # <-- 2 spaces
   ```

2. **Incorrect indentation**
   ```yaml
   # ❌ WRONG
   gitlab:
   base_url: "https://..."  # <-- missing indentation
   
   # ✅ CORRECT
   gitlab:
     base_url: "https://..."  # <-- indented
   ```

3. **Missing quotes around special characters**
   ```yaml
   # ❌ WRONG
   by_path:
     - your-group:subgroup  # <-- colon needs quotes
   
   # ✅ CORRECT
   by_path:
     - "your-group:subgroup"
   ```

**Solution:** Use a YAML validator or check indentation carefully

---

### ❌ Error: "Configuration file not found"

**What it means:** Config file doesn't exist or wrong path

**Solutions:**
```bash
# Check if file exists
ls -la config.yaml

# Create from example if needed
cp config.example.yaml config.yaml

# Or specify path explicitly
gitdoctor -c /path/to/config.yaml -i commits.txt -o results.csv
```

---

## Connection & Authentication

### ❌ Error: "Authentication failed" (401)

**What it means:** GitLab PAT is invalid, expired, or missing

**Solutions:**

1. **Check token is set correctly:**
   ```yaml
   gitlab:
     private_token: "glpat-xxxxxxxxxxxxxxxxxxxx"  # Must start with glpat-
   ```

2. **Verify token hasn't expired:**
   - Go to GitLab → User Settings → Access Tokens
   - Check expiration date
   - Generate new token if expired

3. **Ensure token has correct scopes:**
   - ☑️ `api`
   - ☑️ `read_api`
   - ☑️ `read_repository`

4. **Test token manually:**
   ```bash
   curl -H "PRIVATE-TOKEN: your-token" \
     "https://your-gitlab.com/api/v4/user"
   ```

---

### ❌ Error: "Access forbidden" (403)

**What it means:** You don't have permission to access the resource

**Solutions:**

1. **Check project/group access:**
   - You need at least "Guest" or "Reporter" role
   - Verify you can view the project/group in GitLab web UI

2. **Check group path is correct:**
   ```yaml
   groups:
     by_path:
       - "exact-group-path"  # Must match exactly (case-sensitive)
   ```

3. **Check project path is correct:**
   ```yaml
   projects:
     by_path:
       - "group/subgroup/project"  # Full path with all segments
   ```

---

### ❌ Error: "Resource not found" (404)

**What it means:** Group or project doesn't exist or path is wrong

**Solutions:**

1. **Verify path from GitLab URL:**
   ```
   URL:  https://gitlab.example.com/dfs-core/backend/api-service
   Path: dfs-core/backend/api-service
   ```

2. **Check for typos (case-sensitive):**
   - `dfs-core/DevOps` ≠ `dfs-core/devops`

3. **Try using project ID instead:**
   ```yaml
   projects:
     by_id:
       - 123  # Find in Project Settings → General
   ```

---

### ❌ SSL Certificate Errors

**Error message:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**

**For development/testing (self-signed certificates):**
```yaml
gitlab:
  verify_ssl: false  # ⚠️ Not recommended for production
```

**For production:**
```bash
# Install proper CA certificates
# Mac:
brew install ca-certificates

# Linux:
sudo apt-get install ca-certificates
```

**For corporate proxies:**
```bash
export SSL_CERT_FILE=/path/to/corporate-ca-bundle.crt
export REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
```

---

## Runtime Errors

### ❌ No commits found (but they definitely exist)

**Possible causes:**

1. **Commits are in different projects**
   - Verify commit is in the projects you're searching
   - Run with `-v` to see which projects are searched

2. **Using wrong commit SHA**
   - Use full SHA (40 characters), not abbreviated
   - Example: `a1b2c3d4e5f6789012345678901234567890abcd`

3. **Project is excluded by filters**
   ```yaml
   filters:
     exclude_project_paths:
       - "group/your-project"  # <-- Remove this
   ```

**Debug steps:**
```bash
# 1. Run with verbose logging
gitdoctor -i commits.txt -o results.csv -v

# 2. Check which projects are searched
# Look for: "Will search across X projects"

# 3. Verify commit exists in GitLab UI
# Go to project → Repository → Commits → Search
```

---

### ❌ Error: "Timeout" or very slow

**Causes:**
- Network latency
- GitLab server load
- Too many projects to search

**Solutions:**

1. **Increase timeout:**
   ```yaml
   gitlab:
     timeout_seconds: 30  # Default is 15
   ```

2. **Use explicit mode (faster):**
   ```yaml
   scan:
     mode: "explicit"  # Only search specific projects
   
   projects:
     by_path:
       - "group/project1"  # List only needed projects
   ```

3. **Add exclusions:**
   ```yaml
   filters:
     exclude_project_paths:
       - "group/very-large-repo"
       - "group/archived-project"
   ```

---

### ❌ Rate Limiting (429 errors)

**What it means:** Too many API requests to GitLab

**GitLab limits:**
- gitlab.com: 2,000 requests/minute
- Self-hosted: Admin configurable

**Solutions:**
1. Tool has built-in retry logic - wait and it will resume
2. Reduce number of projects searched
3. Use explicit mode instead of auto-discover

---

## Performance Issues

### ❌ Searches taking too long

**Cause:** Searching too many projects

**Time estimates:**
- 10 projects × 5 commits = ~10-15 seconds
- 50 projects × 5 commits = ~40-60 seconds  
- 100 projects × 5 commits = ~2-3 minutes

**Solutions:**

1. **Switch to explicit mode:**
   ```yaml
   scan:
     mode: "explicit"
   
   projects:
     by_path:
       - "group/critical-project1"
       - "group/critical-project2"
   ```

2. **Use helper script to list projects:**
   ```bash
   python list_projects.py
   cat projects_list.txt  # See all available projects
   ```

3. **Create multiple configs:**
   - `config-quick.yaml` - Top 10 critical projects
   - `config-full.yaml` - All projects (run weekly)

---

## Common Workflow Issues

### ❌ Can't use `gitdoctor` command, only `python -m gitdoctor.cli` works

**Why?** Package not installed, only running source directly

**Fix:**
```bash
cd /path/to/gitdoctor
source venv/bin/activate
pip install -e .

# Now this works:
gitdoctor -i commits.txt -o results.csv
```

---

### ❌ Changes to code not taking effect

**Cause:** Package installed without `-e` flag

**Solution:**
```bash
# Reinstall in editable mode
pip uninstall gitdoctor
pip install -e .

# Now code changes take effect immediately
```

---

## Getting More Help

### Debug Checklist

When reporting issues, include:

1. **Verbose output:**
   ```bash
   gitdoctor -i commits.txt -o results.csv -v > debug.log 2>&1
   ```

2. **Configuration (with token removed):**
   ```bash
   cat config.yaml | grep -v private_token
   ```

3. **Python and package versions:**
   ```bash
   python --version
   pip list | grep gitdoctor
   ```

4. **Test GitLab connection manually:**
   ```bash
   curl -I https://your-gitlab.com
   ```

### Additional Resources

- **README.md** - Full documentation
- **QUICKSTART.md** - 5-minute setup guide
- **EXPLICIT_MODE_GUIDE.md** - Fast searching guide
- **INTEGRATION_TESTING_GUIDE.md** - Testing with real GitLab
- **YOUR_TESTING_GUIDE.md** - Comprehensive testing

---

## Quick Reference: Common Fixes

| Error | Quick Fix |
|-------|-----------|
| "explicit mode requires projects" | Use `- "path"` not `"path",` in config |
| "gitdoctor command not found" | Run `pip install -e .` |
| "Authentication failed" | Check PAT in config.yaml |
| "Resource not found" | Verify group/project path in GitLab UI |
| "SSL error" | Set `verify_ssl: false` for testing |
| Searches too slow | Use explicit mode, list only needed projects |
| No commits found | Run with `-v`, check project list |

---

**Still having issues?** Check the README.md Troubleshooting section or review the integration testing guide.

