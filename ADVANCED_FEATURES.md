# GitDoctor Advanced Features Guide

This guide covers the advanced features added to GitDoctor:
- **HTML Report Generator** - Beautiful visual reports
- **Slack Notifications** - Automatic notifications
- **JIRA Integration** - Automatic ticket linking

---

## 🎨 HTML Report Generator

Generate beautiful, interactive HTML reports instead of CSV files.

### Basic Usage

```bash
# Generate HTML report
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta-report.html \
  --format html
```

### Features

- **Summary Statistics** - Visual cards showing key metrics
- **Project Breakdown** - Color-coded project cards (green=changes, red=errors, gray=no changes)
- **Commits Table** - Interactive table with all commits
- **JIRA Tickets** - If JIRA is configured, shows ticket links
- **Responsive Design** - Works on desktop and mobile
- **Self-Contained** - Single HTML file, no external dependencies

### Example

```bash
gitdoctor delta \
  --base MobiquityPay_vX.10.15.2_PVG.B1 \
  --target MobiquityPay_v11.0.0_20250908_PVG.B1 \
  -o release-report.html \
  --format html \
  --jira-url https://jira.company.com \
  --jira-project MON
```

**Output:** Opens `release-report.html` in your browser with a beautiful, interactive report!

---

## 📢 Slack Notifications

Send automatic notifications to Slack when delta discovery completes.

### Setup

1. **Create a Slack Webhook:**
   - Go to your Slack workspace
   - Apps → Incoming Webhooks
   - Create a new webhook
   - Copy the webhook URL

2. **Use in Command:**

```bash
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Notification Content

The Slack message includes:
- Base and target references
- Number of projects searched
- Total commits found
- Files changed
- Link to generated report
- Color-coded status (green=success, red=errors)

### Example Slack Message

```
🔍 GitDoctor Delta Discovery Complete

Base Reference: v1.0.0
Target Reference: v2.0.0
Projects Searched: 25
Projects with Changes: 18
Total Commits: 342
Files Changed: 1,247

📄 Report generated: delta.csv
```

---

## 🎫 JIRA Integration

Automatically extract and link JIRA tickets from commit messages.

### Features

- **Automatic Extraction** - Finds ticket patterns like `MON-12345`, `JIRA-456`
- **CSV Integration** - Adds `jira_tickets` and `jira_ticket_urls` columns
- **HTML Integration** - Shows clickable ticket links in HTML reports
- **Ticket Summary** - Displays summary of all tickets found

### Setup

```bash
# Basic usage - extract all ticket patterns
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv \
  --jira-url https://jira.company.com

# Filter by project key (e.g., only MON tickets)
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv \
  --jira-url https://jira.company.com \
  --jira-project MON
```

### Supported Ticket Patterns

- `MON-12345` ✅
- `JIRA-456` ✅
- `PROJECT-789` ✅
- `ABC-12345` ✅

### CSV Output

New columns added:
- `jira_tickets` - Pipe-separated list of ticket IDs (e.g., `MON-12345|MON-12346`)
- `jira_ticket_urls` - Pipe-separated list of ticket URLs

### HTML Output

- Tickets appear as clickable badges in the commits table
- Dedicated "JIRA Tickets" section with summary
- Shows ticket count and affected projects

### Example Output

After running with JIRA integration:

```
============================================================
JIRA Tickets Found
============================================================
MON-12345: 5 commit(s) in 3 project(s)
  URL: https://jira.company.com/browse/MON-12345
MON-12346: 2 commit(s) in 1 project(s)
  URL: https://jira.company.com/browse/MON-12346
============================================================
```

---

## 🚀 Combined Usage Examples

### Example 1: Full Featured Report

```bash
# Generate HTML report with JIRA links and send Slack notification
gitdoctor delta \
  --base MobiquityPay_vX.10.15.2_PVG.B1 \
  --target MobiquityPay_v11.0.0_20250908_PVG.B1 \
  -o release-v11-report.html \
  --format html \
  --jira-url https://jira.company.com \
  --jira-project MON \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -v
```

**What this does:**
1. ✅ Compares the two tags across all configured projects
2. ✅ Generates beautiful HTML report
3. ✅ Extracts and links MON-* JIRA tickets
4. ✅ Sends summary to Slack
5. ✅ Shows detailed progress in verbose mode

### Example 2: CSV with JIRA for Analysis

```bash
# Generate CSV with JIRA tickets for Excel analysis
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta-with-tickets.csv \
  --jira-url https://jira.company.com \
  --jira-project MON
```

**Then in Excel:**
- Filter by `jira_tickets` column
- Group by ticket to see all commits for each ticket
- Click `jira_ticket_urls` to open tickets

### Example 3: Quick Notification Only

```bash
# Just get notified when delta completes
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 📋 Configuration Tips

### Environment Variables (Optional)

You can set these in your environment to avoid passing on command line:

```bash
export GITDOCTOR_SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export GITDOCTOR_JIRA_URL="https://jira.company.com"
export GITDOCTOR_JIRA_PROJECT="MON"
```

Then use in scripts:
```bash
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.html \
  --format html \
  --slack-webhook "$GITDOCTOR_SLACK_WEBHOOK" \
  --jira-url "$GITDOCTOR_JIRA_URL" \
  --jira-project "$GITDOCTOR_JIRA_PROJECT"
```

### Config File (Future Enhancement)

We could add these to `config.yaml` in the future:
```yaml
notifications:
  slack:
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  
jira:
  base_url: "https://jira.company.com"
  project_key: "MON"
```

---

## 🎯 Use Cases

### 1. Release Management

```bash
# Before release, generate comprehensive report
gitdoctor delta \
  --base v1.0-rc \
  --target v2.0-rc \
  -o pre-release-report.html \
  --format html \
  --jira-url https://jira.company.com \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Result:** Beautiful HTML report shared in Slack with all tickets linked!

### 2. Weekly Change Summary

```bash
# Weekly automated report
gitdoctor delta \
  --base $(git describe --tags --abbrev=0) \
  --target HEAD \
  -o weekly-changes.html \
  --format html \
  --jira-url https://jira.company.com \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Result:** Automated weekly summary sent to team Slack channel!

### 3. Hotfix Verification

```bash
# Quick hotfix check with notification
gitdoctor delta \
  --base v2.0.0 \
  --target v2.0.1 \
  -o hotfix-check.html \
  --format html \
  --jira-url https://jira.company.com \
  --jira-project HOTFIX \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Result:** Instant notification when hotfix delta is ready!

---

## 🔧 Troubleshooting

### Slack Notifications Not Working

**Check:**
1. Webhook URL is correct
2. Webhook is active in Slack
3. Network connectivity to Slack

**Debug:**
```bash
# Test with verbose mode
gitdoctor delta --base v1.0 --target v2.0 -o test.csv \
  --slack-webhook YOUR_WEBHOOK -v
```

### JIRA Tickets Not Found

**Check:**
1. JIRA URL is correct (no trailing slash)
2. Ticket pattern matches (e.g., `MON-12345`)
3. Project key filter is correct (if using `--jira-project`)

**Debug:**
```bash
# Extract all ticket patterns (no project filter)
gitdoctor delta --base v1.0 --target v2.0 -o test.csv \
  --jira-url https://jira.company.com -v
```

### HTML Report Not Opening

**Check:**
1. File was generated successfully
2. File permissions are correct
3. Browser supports modern HTML/CSS

**Try:**
```bash
# Open in default browser
open delta-report.html  # Mac
xdg-open delta-report.html  # Linux
start delta-report.html  # Windows
```

---

## 📚 Related Documentation

- **[DELTA_GUIDE.md](DELTA_GUIDE.md)** - Complete delta discovery guide
- **[README.md](README.md)** - Main documentation
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues

---

## 🎉 Summary

**New Features:**
- ✅ HTML reports with beautiful visualizations
- ✅ Slack notifications for team updates
- ✅ JIRA ticket extraction and linking
- ✅ Enhanced CSV with JIRA columns
- ✅ All features work together seamlessly

**Try it now:**
```bash
gitdoctor delta \
  --base YOUR_BASE_TAG \
  --target YOUR_TARGET_TAG \
  -o report.html \
  --format html \
  --jira-url YOUR_JIRA_URL \
  --slack-webhook YOUR_SLACK_WEBHOOK
```

Enjoy your enhanced GitDoctor experience! 🚀

