# GitDoctor Demo Script - Delta Discovery

**Purpose:** Show how to identify all changes between two release tags

**Tags to Compare:**
- **Base (Older):** `MobiquityPay_vX.10.15.8_L4Patch_19Jan26` (Docker: X.10.15)
- **Target (Newer):** `MobiquityPay_vX.10.15.8_PVG.B1` (Docker: X.10.15.8)

**Audience:** Cross-functional teams, PE teams

**Duration:** ~10 minutes

---

## 🎬 Demo Script

### Part 1: Introduction (1 min)

**Say:**
> "Today I'll show you GitDoctor - a tool that helps us identify exactly what changed between two releases across all our microservices. This is crucial for deployment planning, test selection, and risk assessment."

**Show on screen:**
- GitDoctor repository: https://github.com/javedansari-foundry/gitdoctor
- Documentation: README.md and TEAM_QUICKSTART.md

---

### Part 2: Setup Verification (1 min)

**Say:**
> "First, let me verify GitDoctor is installed and configured."

**Commands:**

```bash
# Navigate to GitDoctor directory
cd /Users/javedansari/My\ Projects/GitDoctor/gitdoctor

# Activate virtual environment
source venv/bin/activate

# Verify installation
gitdoctor --version
```

**Expected output:** `gitdoctor 1.0.0`

**Say:**
> "Great! GitDoctor is installed. It's already configured to connect to our GitLab instance."

---

### Part 3: Show Configuration (30 seconds)

**Say:**
> "Let me show you the configuration file briefly."

**Command:**

```bash
# Show key config settings (sanitized)
cat config.yaml | grep -A 5 "^gitlab:" | grep -v "private_token"
```

**Say:**
> "GitDoctor is configured to search across all projects in the dfs-core group, which includes all our microservices."

---

### Part 4: Run Delta Discovery (2 min)

**Say:**
> "Now, let's find all changes between two tags:
> - Base tag: MobiquityPay_vX.10.15.8_L4Patch_19Jan26 (the older release)
> - Target tag: MobiquityPay_vX.10.15.8_PVG.B1 (the newer release)
> 
> This will search across ALL our microservices and find every commit that's in the new tag but not in the old one."

**Command:**

```bash
gitdoctor delta \
  --base MobiquityPay_vX.10.15.8_L4Patch_19Jan26 \
  --target MobiquityPay_vX.10.15.8_PVG.B1 \
  --format html \
  -o delta-X.10.15-to-X.10.15.8.html \
  -v
```

**While running, say:**
> "GitDoctor is now:
> 1. Connecting to GitLab
> 2. Discovering all projects in our dfs-core group
> 3. For each project, fetching commits from both tags
> 4. Computing the delta - commits in target but not in base
> 5. Extracting JIRA tickets from commit messages
> 6. Generating an HTML report"

**Wait for completion** (~30-60 seconds depending on number of projects)

---

### Part 5: Show Summary Output (1 min)

**Say:**
> "Let's look at the summary that GitDoctor provides."

**Expected output on terminal:**
```
======================================================================
Delta Discovery Summary
======================================================================
Base Reference:          MobiquityPay_vX.10.15.8_L4Patch_19Jan26
Target Reference:        MobiquityPay_vX.10.15.8_PVG.B1
Projects Searched:       [X number]
Projects with Changes:   [X number]
Projects without Changes: [X number]

Commits in Base Ref:     [X number]
Commits in Target Ref:   [X number]
Delta (Unique to Target): [X number]

JIRA Tickets: [list of tickets]

Top Projects by Commit Count:
  1. project-name: [X] commits
  ...
======================================================================
```

**Say:**
> "This tells us:
> - How many projects were analyzed
> - How many commits are NEW in the target release
> - Which JIRA tickets are included
> - Which projects have the most changes"

---

### Part 6: Open HTML Report (3 min)

**Say:**
> "Now let's open the detailed HTML report."

**Command:**

```bash
# Open HTML report in default browser
open delta-X.10.15-to-X.10.15.8.html
```

**Point out these sections in the report:**

1. **Summary Section**
   - Total projects analyzed
   - Total commits in delta
   - JIRA tickets with clickable links

2. **JIRA Tickets Section**
   - List of all tickets
   - How many commits per ticket
   - Direct links to JIRA

3. **Delta Commits by Project**
   - One section per project with changes
   - Each commit shows:
     - Commit message
     - Author
     - Date
     - Link to GitLab

**Say:**
> "This report gives us complete traceability:
> - Every commit that's being deployed
> - Which developer made each change
> - Which JIRA stories are included
> - Direct links to both GitLab and JIRA"

---

### Part 7: Export for Test Planning (1 min)

**Say:**
> "We can also export in CSV format for spreadsheet analysis and test planning."

**Command:**

```bash
gitdoctor delta \
  --base MobiquityPay_vX.10.15.8_L4Patch_19Jan26 \
  --target MobiquityPay_vX.10.15.8_PVG.B1 \
  --format csv \
  -o delta-X.10.15-to-X.10.15.8.csv
```

**Say:**
> "This CSV can be imported into Excel or used for automated test selection."

**Command:**

```bash
# Show first few lines of CSV
head -10 delta-X.10.15-to-X.10.15.8.csv
```

---

### Part 8: MR Changes for Test Selection (2 min)

**Say:**
> "GitDoctor also has a new feature for intelligent test selection. If you know a specific MR that's part of this release, you can get ALL the file changes."

**Command:**

```bash
# Example with a real MR from your project
gitdoctor mr-changes \
  --project "dfs-core/product-domains/transaction/shulka" \
  --mr 123 \
  --format test-selection \
  -o mr-changes-example.json
```

**Say:**
> "This extracts:
> - All commits in the MR
> - Every file that changed
> - Which directories were affected
> - JIRA tickets
> - Separation of test files vs source code
> 
> Perfect for determining which test suites to run."

---

### Part 9: Use Cases (1 min)

**Say:**
> "Let me summarize the key use cases for different teams:

**For QA/Test Teams:**
- Identify which features changed → plan test coverage
- Extract JIRA tickets → map to test cases
- Get file changes → select relevant test suites

**For Release Managers:**
- Complete audit trail of what's being deployed
- JIRA ticket tracking for release notes
- Risk assessment based on number of changes

**For DevOps/PE Teams:**
- Automate deployment validation
- Generate release documentation
- Track changes across microservices

**For Developers:**
- Review what's included in a release
- Verify your commits made it to the tag
- Debug deployment issues"

---

### Part 10: Getting Started (1 min)

**Say:**
> "Your team can start using GitDoctor today. Here's how:"

**Show on screen:**

```
Step 1: Clone repository
git clone https://github.com/javedansari-foundry/gitdoctor.git

Step 2: Install
cd gitdoctor
python3 -m venv venv
source venv/bin/activate
pip install -e .

Step 3: Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your GitLab token

Step 4: Run your first command
gitdoctor delta --base TAG1 --target TAG2 -o output.html
```

**Say:**
> "Full documentation is in:
> - TEAM_QUICKSTART.md - for getting started
> - README.md - for complete reference
> - DELTA_GUIDE.md - for delta discovery
> - MR_CHANGES_GUIDE.md - for test selection"

---

### Part 11: Q&A Preview (30 seconds)

**Say:**
> "Common questions:

**Q: How long does it take?**
A: Usually 30-60 seconds for ~50 projects. Depends on number of commits.

**Q: Can I filter by date?**
A: Yes! Use --after and --before flags to filter commits by date.

**Q: Does it work with branches too?**
A: Yes! You can compare tags, branches, or even specific commit SHAs.

**Q: Can I automate this in CI/CD?**
A: Absolutely! GitDoctor is designed for automation. JSON and CSV output formats are perfect for parsing."

---

## 📋 Post-Demo Resources

**Share with attendees:**

1. **Repository:** https://github.com/javedansari-foundry/gitdoctor
2. **Quick Start:** TEAM_QUICKSTART.md
3. **Demo Commands:** (this file)
4. **Sample Output:** 
   - delta-X.10.15-to-X.10.15.8.html
   - delta-X.10.15-to-X.10.15.8.csv

**Support Channels:**
- Documentation in repository
- Team chat for questions
- GitHub issues for bugs/feature requests

---

## 🎯 Key Messages to Emphasize

1. ✅ **Automated** - No more manual `git log` in each repo
2. ✅ **Complete** - Searches ALL microservices automatically
3. ✅ **Traceable** - JIRA tickets extracted and linked
4. ✅ **Multiple Formats** - HTML, CSV, JSON for different needs
5. ✅ **Fast** - Results in under a minute
6. ✅ **Enterprise Ready** - Works with self-hosted GitLab

---

## 🔧 Troubleshooting During Demo

**If command fails:**
```bash
# Check GitLab connection
gitdoctor --version

# Verify config
cat config.yaml | grep base_url

# Try with verbose mode
gitdoctor delta --base TAG1 --target TAG2 -v -o output.csv
```

**If tags not found:**
- Tag names might be slightly different
- Use GitLab UI to verify exact tag names
- Tags might not exist in all projects (this is OK, GitDoctor handles it)

**If running slowly:**
- Normal for first run (no cache)
- Add date filters to reduce commits:
  ```bash
  gitdoctor delta --base TAG1 --target TAG2 --after 2026-01-01 -o output.csv
  ```

---

## ✅ Pre-Demo Checklist

- [ ] GitDoctor installed and working (`gitdoctor --version`)
- [ ] Virtual environment activated
- [ ] config.yaml configured with valid token
- [ ] Test connection to GitLab works
- [ ] Screen recording software ready
- [ ] Terminal font size large enough for recording
- [ ] Browser ready to open HTML reports
- [ ] This script printed or on second screen
- [ ] Example output files ready to show (if demo fails)

---

**Good luck with your demo! 🚀**

