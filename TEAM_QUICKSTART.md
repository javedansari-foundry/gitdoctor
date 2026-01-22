# GitDoctor Team Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/javedansari-foundry/gitdoctor.git
cd gitdoctor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install GitDoctor
pip install -e .

# Verify installation
gitdoctor --version
```

### Step 2: Configure GitLab Access

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml with your details
nano config.yaml  # or use your preferred editor
```

**Required settings:**
```yaml
gitlab:
  base_url: "http://blrgitlab.comviva.com"
  private_token: "YOUR_GITLAB_TOKEN_HERE"
  verify_ssl: false

jira:
  base_url: "https://comviva.atlassian.net"
  project_key: "MON"  # Optional: your project key
```

**Get your GitLab token:**
1. Go to: http://blrgitlab.comviva.com/-/profile/personal_access_tokens
2. Create token with scopes: `api`, `read_api`, `read_repository`
3. Copy token to `config.yaml`

### Step 3: Run Your First Command

```bash
# Extract changes from an MR for test selection
gitdoctor mr-changes --project 127 --mr 123 -o test-input.json
```

---

## 📖 Main Use Cases

### 1️⃣ Intelligent Test Selection (NEW!)

**Goal:** Know exactly what changed in an MR to run only relevant tests.

```bash
# Get MR changes in test-selection format
gitdoctor mr-changes \
  --project "dfs-core/product-domains/transaction/shulka" \
  --mr 456 \
  --format test-selection \
  -o test-input.json
```

**Output includes:**
- ✅ All commits and changed files
- ✅ JIRA tickets (e.g., MON-126043)
- ✅ Changed directories
- ✅ File extensions and types
- ✅ Separation of source vs test files

**📖 Full Guide:** [MR_CHANGES_GUIDE.md](MR_CHANGES_GUIDE.md)

### 2️⃣ Compare Releases (Delta Discovery)

**Goal:** Find all changes between two releases/tags/branches.

```bash
# Compare two tags across all services
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv
```

**📖 Full Guide:** [DELTA_GUIDE.md](DELTA_GUIDE.md)

### 3️⃣ Search for Commits

**Goal:** Find which projects contain specific commits.

```bash
# Create a file with commit SHAs (one per line)
echo "abc123def456" > commits.txt

# Search across projects
gitdoctor search -i commits.txt -o results.csv
```

### 4️⃣ Track Merge Requests

**Goal:** Find all MRs merged to a branch in a date range.

```bash
# Find MRs merged to master in last 3 months
gitdoctor mr \
  --target master \
  --after 2025-10-01 \
  -o merged-mrs.csv
```

---

## 🎯 Common Commands for Your Team

### For QA/Test Engineers

```bash
# Get MR changes for test planning
gitdoctor mr-changes --project 127 --mr 456 -o mr-changes.json

# Get detailed changes with full diffs
gitdoctor mr-changes --project 127 --mr 456 \
  --format test-selection-detailed \
  -o detailed-changes.json
```

### For Release Managers

```bash
# Compare releases to see what's being deployed
gitdoctor delta \
  --base premaster-291225 \
  --target master \
  --after 2025-12-01 \
  -o deployment-delta.csv

# Export as HTML report
gitdoctor delta \
  --base premaster-291225 \
  --target master \
  --format html \
  -o deployment-report.html
```

### For DevOps/CI Engineers

```bash
# Get MR changes without diffs (faster for CI)
gitdoctor mr-changes --project 127 --mr 456 --no-diffs -o changes.json

# Use in CI pipeline (example)
#!/bin/bash
MR_IID=$(echo $CI_MERGE_REQUEST_IID)
PROJECT_ID=$(echo $CI_PROJECT_ID)

gitdoctor mr-changes \
  --project $PROJECT_ID \
  --mr $MR_IID \
  --format test-selection \
  -o test-input.json

# Parse and run tests based on changes
python3 test-selector.py test-input.json
```

---

## 📋 Project IDs (Quick Reference)

Common project IDs for your team:

| Project | ID | Path |
|---------|----|----|
| Shulka | 127 | dfs-core/product-domains/transaction/shulka |
| SOE | TBD | dfs-core/mobiquity-one-issuing/microservices/soe |
| SOE Core | TBD | dfs-core/orchestration/soe-core |

**Find project ID:**
```bash
# Visit project in GitLab, check URL or use API
curl -H "PRIVATE-TOKEN: your-token" \
  "http://blrgitlab.comviva.com/api/v4/projects/dfs-core%2Fproduct-domains%2Ftransaction%2Fshulka" \
  | jq '.id'
```

---

## 🆘 Troubleshooting

### Issue: "Project not found"
**Solution:** Use project ID instead of path, or check if you have access.

```bash
# Try with ID
gitdoctor mr-changes --project 127 --mr 123 -o output.json
```

### Issue: "Connection failed" or SSL errors
**Solution:** Already configured in `config.yaml` with `verify_ssl: false`

### Issue: "MR not found"
**Solution:** Verify MR IID (the number in !123, not the internal ID)

### Issue: "Command too slow"
**Solution:** Use `--no-diffs` flag for faster processing

```bash
gitdoctor mr-changes --project 127 --mr 456 --no-diffs -o output.json
```

---

## 📚 Documentation Index

| Guide | Purpose | Link |
|-------|---------|------|
| **MR Changes Guide** | Complete guide for test selection | [MR_CHANGES_GUIDE.md](MR_CHANGES_GUIDE.md) |
| **Delta Guide** | Compare releases/tags | [DELTA_GUIDE.md](DELTA_GUIDE.md) |
| **Main README** | Full feature documentation | [README.md](README.md) |
| **Development Rules** | For contributors | [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) |

---

## 💡 Tips for Your Team

1. **Use test-selection format** - It's optimized for automation
2. **Configure JIRA in config.yaml** - Automatic ticket extraction
3. **Use project IDs** - Faster than paths
4. **Add --no-diffs** - For faster CI/CD integration
5. **Create aliases** - Save common commands

**Example alias:**
```bash
# Add to ~/.bashrc or ~/.zshrc
alias gd-mr="gitdoctor mr-changes --project 127"

# Usage
gd-mr --mr 456 -o output.json
```

---

## 🤝 Getting Help

- **Documentation:** Check guides in the repository
- **Issues:** Create GitHub issue if you find bugs
- **Questions:** Ask in team chat or check existing docs

---

## 📌 Next Steps

1. ✅ Clone repository and install
2. ✅ Configure `config.yaml` with your token
3. ✅ Test with a known MR: `gitdoctor mr-changes --project 127 --mr <MR_NUMBER> -o test.json`
4. 📖 Read [MR_CHANGES_GUIDE.md](MR_CHANGES_GUIDE.md) for complete examples
5. 🚀 Integrate with your test selection workflow

---

**Ready to go! 🎉**

For detailed examples and advanced usage, see [MR_CHANGES_GUIDE.md](MR_CHANGES_GUIDE.md)

