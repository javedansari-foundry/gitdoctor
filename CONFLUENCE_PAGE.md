# GitDoctor - Automated Release Delta Discovery & Intelligent Test Selection

> **Version:** 1.1.0  
> **Repository:** [http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor](http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor)  
> **Last Updated:** January 2026

---

## 🎯 What is GitDoctor?

GitDoctor automates release tracking and test selection across multiple GitLab repositories:

- **🔍 Delta Discovery** - Find all commits between any two tags/branches across all repos
- **📊 Release Reports** - Generate beautiful HTML/CSV reports in seconds
- **🎫 JIRA Integration** - Auto-extract and link JIRA tickets from commits
- **🧪 Test Selection** - Identify exact changes in Merge Requests for targeted testing
- **⚡ Speed** - 60 seconds vs 2-4 hours of manual work per release

---

## 💡 Why Use GitDoctor?

| Manual Process | With GitDoctor |
|----------------|----------------|
| 2-4 hours per release | **60 seconds** ⚡ |
| Run `git log` in 30+ repos | **Single command** 🎯 |
| Copy-paste to Excel | **Auto-generated reports** 📊 |
| Miss commits & repos | **100% accuracy** ✅ |
| No JIRA correlation | **Auto-linked tickets** 🎫 |
| Manual test selection | **Intelligent recommendations** 🧪 |

---

## 👥 Who Should Use It?

- **Release Managers** - Track what's going to production
- **QA Teams** - Know exactly what to test and why
- **DevOps/PE Teams** - Verify deployments and hotfixes
- **Developers** - Find where commits landed across repos
- **Auditors** - Generate compliance & change reports

---

## ⚡ Quick Commands

### 1️⃣ Compare Two Releases (Delta)

```bash
# Generate HTML report showing all changes between tags
gitdoctor delta --base MobiquityPay_vX.10.15.8 --target MobiquityPay_vX.10.16.0 \
  -o release-delta.html --format html
```

**Output:** All commits, changed files, JIRA tickets, visual charts

### 2️⃣ Get Merge Request Changes (for Test Selection)

```bash
# Extract exact changes from a specific MR
gitdoctor mr-changes --project "dfs-core/transaction/shulka" --mr-id 1234 \
  -o mr-changes.json --format test-selection
```

**Output:** Changed files, diffs, test recommendations, JIRA tickets

### 3️⃣ Search Commits Across Repos

```bash
# Find where specific commits landed
gitdoctor search -f commits.txt -o results.csv
```

---

## 🎯 Key Features

| Feature | Description | Command |
|---------|-------------|---------|
| **Delta Discovery** | Compare tags/branches across all repos | `gitdoctor delta` |
| **MR Changes** | Extract exact changes for test selection | `gitdoctor mr-changes` |
| **HTML Reports** | Interactive reports with charts & filters | `--format html` |
| **JIRA Integration** | Auto-link tickets from commit messages | Built-in |
| **Multi-Format Output** | CSV, JSON, HTML, test-selection | `--format <type>` |
| **Date Filtering** | Scope by time range | `--after`, `--before` |

---

## 🚀 Getting Started (5 Minutes)

### Step 1: Clone Repository

```bash
git clone http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor.git
cd gitdoctor
```

### Step 2: Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Step 3: Configure

Copy `config.comviva.yaml` to `config.yaml` and update your token:

```yaml
gitlab:
  base_url: "http://blrgitlab.comviva.com"
  private_token: "your-gitlab-token"  # Get from: GitLab → Settings → Access Tokens
```

### Step 4: Run Your First Command

```bash
# Compare two releases
gitdoctor delta --base MobiquityPay_vX.10.15.8 --target MobiquityPay_vX.10.16.0 \
  -o delta.html --format html

# Open the report
open delta.html
```

✅ **Done!** You now have a complete release report with all commits, JIRA tickets, and visual charts.

📚 **Need more details?** See `QUICKSTART.md` in the repository.

---

## 📋 Common Use Cases

### 1. Release Notes Generation

```bash
# What's new in the upcoming release?
gitdoctor delta --base MobiquityPay_vX.10.15.8 --target MobiquityPay_vX.10.16.0 \
  -o release-notes.html --format html
```

**Output:** Complete changelog with all commits, authors, and JIRA tickets

### 2. Hotfix Verification

```bash
# What went into the L4 patch?
gitdoctor delta --base MobiquityPay_vX.10.15.8_PVG.B1 \
               --target MobiquityPay_vX.10.15.8_L4Patch_19Jan26 \
  -o hotfix-verification.csv
```

**Output:** Exact list of fixes for QA testing

### 3. Test Selection for MR

```bash
# What should we test for this merge request?
gitdoctor mr-changes --project "dfs-core/transaction/shulka" --mr-id 1234 \
  -o test-selection.json --format test-selection
```

**Output:** Changed files with diffs, recommended test suites, JIRA tickets

### 4. Deployment Audit

```bash
# Generate compliance report for auditors
gitdoctor delta --base prod-release-v1 --target prod-release-v2 \
  -o audit-report.html --format html
```

**Output:** Official record of what was deployed

---

## 📖 Detailed Documentation

All comprehensive guides are in the repository:

| Document | Purpose | Location |
|----------|---------|----------|
| `README.md` | Overview & setup | Repository root |
| `QUICKSTART.md` | 5-minute getting started | Repository root |
| `config.comviva.yaml` | Comviva-specific config template | Repository root |
| `DELTA_GUIDE.md` | Complete delta command reference | Repository root |
| `MR_CHANGES_GUIDE.md` | MR changes & test selection | Repository root |
| `TROUBLESHOOTING.md` | Common issues & solutions | Repository root |
| `DEMO_SCRIPT.md` | Recording/demo script | Repository root |

---

## ❓ Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| **401 Unauthorized** | Regenerate GitLab token with `read_api` scope |
| **Base ref not found** | Normal - not all repos have all tags (check CSV) |
| **0 commits found** | Check direction: `--base` (older) `--target` (newer) |
| **Slow performance** | Increase `timeout_seconds` in config or use explicit mode |

**Need more help?** See `TROUBLESHOOTING.md` in the repository or run with `-v` flag for detailed logging.

---

## 🆕 What's New in v1.1.0 (January 2026)

✅ **MR Changes Command** - Extract exact changes from Merge Requests for intelligent test selection  
✅ **Test Selection Format** - New output format optimized for automated test case selection  
✅ **CSV Export Fix** - Fixed multiline commit message handling in CSV exports  
✅ **Comviva Config** - Pre-configured `config.comviva.yaml` for internal use  
✅ **Demo Scripts** - Ready-to-use recording scripts for team presentations

---

## 📞 Support & Contact

**Repository:** [http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor](http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor)

**For Issues:**
1. Run command with `-v` flag to get detailed logs
2. Check `TROUBLESHOOTING.md` in the repository
3. Contact Platform Engineering team

**Quick Links:**
- 📚 Full Documentation: See `README.md` in repository
- 🚀 Quick Start: See `QUICKSTART.md`  
- 🎬 Demo Guide: See `DEMO_SCRIPT.md`
- ⚙️ Configuration: See `config.comviva.yaml`

---

*Last updated: January 2026 | Version 1.1.0*






