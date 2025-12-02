# JIRA & Teams Setup Guide

Quick guide to set up JIRA integration and Teams notifications for GitDoctor.

---

## 🎫 JIRA Integration

### ✅ **Good News: No Access Token Needed!**

JIRA integration in GitDoctor **does NOT require any access tokens or authentication**. 

**How it works:**
- GitDoctor extracts JIRA ticket patterns from commit messages (e.g., `MON-12345`)
- It creates clickable links to your JIRA instance
- No API calls are made - it's just URL generation!

### What You Need

**Only 2 things:**

1. **JIRA Base URL** - Your JIRA instance URL
   - Example: `https://jira.company.com`
   - Example: `https://yourcompany.atlassian.net`
   - **No trailing slash!**

2. **Project Key (Optional)** - If you want to filter tickets
   - Example: `MON` (to only extract MON-* tickets)
   - If not specified, extracts ALL ticket patterns

### How to Find Your JIRA URL

1. Open any JIRA ticket in your browser
2. Look at the URL: `https://jira.company.com/browse/MON-12345`
3. The base URL is: `https://jira.company.com`

### Testing JIRA Integration

```bash
# Test with your JIRA URL
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  -o test-with-jira.csv \
  --jira-url https://YOUR_JIRA_URL_HERE \
  --jira-project MON \
  -v
```

**What to expect:**
- CSV will have `jira_tickets` and `jira_ticket_urls` columns
- HTML reports will show clickable ticket badges
- Summary will show all tickets found

### Example Output

After running, you'll see:
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

## 💬 Microsoft Teams Notifications

### Setup Steps

1. **Create a Teams Webhook:**
   - Open Microsoft Teams
   - Go to the channel where you want notifications
   - Click **⋯** (three dots) next to channel name
   - Select **Connectors**
   - Search for **"Incoming Webhook"**
   - Click **Configure**
   - Give it a name (e.g., "GitDoctor")
   - Click **Create**
   - **Copy the webhook URL** (you'll need this!)

2. **Use in GitDoctor:**

```bash
gitdoctor delta \
  --base v1.0.0 \
  --target v2.0.0 \
  -o delta.csv \
  --teams-webhook https://outlook.office.com/webhook/YOUR_WEBHOOK_URL
```

### Testing Teams Notification

```bash
# Test with your Teams webhook
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  -o test-delta.csv \
  --teams-webhook https://outlook.office.com/webhook/YOUR_WEBHOOK_URL \
  -v
```

**What to expect:**
- A message card will appear in your Teams channel
- Shows summary statistics
- Color-coded (green=success, red=errors)
- Includes link to generated report

### Teams Message Format

The notification will show:
- 🔍 **Title:** GitDoctor Delta Discovery Complete
- **Base Reference:** Your base tag
- **Target Reference:** Your target tag
- **Projects Searched:** Number
- **Projects with Changes:** Number
- **Total Commits:** Number
- **Files Changed:** Number

---

## 📧 Email Notifications (Optional)

If you prefer email instead of Teams, you can use SMTP:

```bash
# Email requires SMTP configuration
# This would need to be added to config.yaml or CLI args
# For now, Teams webhook is simpler!
```

---

## 🚀 Complete Example: JIRA + Teams

```bash
# Full featured command with JIRA and Teams
gitdoctor delta \
  --base release-v1.0.0 \
  --target release-v2.0.0 \
  -o release-report.html \
  --format html \
  --jira-url https://YOUR_JIRA_URL \
  --jira-project MON \
  --teams-webhook https://outlook.office.com/webhook/YOUR_WEBHOOK_URL \
  -v
```

**This will:**
1. ✅ Compare the two tags
2. ✅ Generate HTML report with JIRA ticket links
3. ✅ Extract MON-* tickets from commits
4. ✅ Send notification to Teams channel
5. ✅ Show detailed progress

---

## ❓ Common Questions

### Q: Do I need JIRA access token?
**A:** No! GitDoctor only extracts ticket patterns and creates URLs. No API authentication needed.

### Q: What if I don't know my JIRA URL?
**A:** 
1. Open any JIRA ticket
2. Look at the browser URL
3. Remove `/browse/TICKET-ID` part
4. That's your base URL!

### Q: How do I get Teams webhook?
**A:**
1. Teams → Channel → ⋯ → Connectors
2. Search "Incoming Webhook"
3. Configure → Create
4. Copy the URL

### Q: Can I use both JIRA and Teams?
**A:** Yes! They work together perfectly.

### Q: What ticket patterns are supported?
**A:** Any pattern like `PROJECT-12345`:
- `MON-12345` ✅
- `JIRA-456` ✅
- `ABC-789` ✅
- `PROJECT-12345` ✅

---

## 🧪 Quick Test Commands

### Test 1: JIRA Only
```bash
gitdoctor delta \
  --base YOUR_BASE_TAG \
  --target YOUR_TARGET_TAG \
  -o test-jira.csv \
  --jira-url https://YOUR_JIRA_URL \
  --jira-project MON \
  -v
```

### Test 2: Teams Only
```bash
gitdoctor delta \
  --base YOUR_BASE_TAG \
  --target YOUR_TARGET_TAG \
  -o test.csv \
  --teams-webhook https://outlook.office.com/webhook/YOUR_WEBHOOK \
  -v
```

### Test 3: Both Together
```bash
gitdoctor delta \
  --base YOUR_BASE_TAG \
  --target YOUR_TARGET_TAG \
  -o test-full.html \
  --format html \
  --jira-url https://YOUR_JIRA_URL \
  --jira-project MON \
  --teams-webhook https://outlook.office.com/webhook/YOUR_WEBHOOK \
  -v
```

---

## 📝 What Information Do I Need?

### For JIRA:
- ✅ JIRA base URL (e.g., `https://jira.company.com`)
- ✅ Project key (optional, e.g., `MON`)
- ❌ **NO access token needed!**
- ❌ **NO project ID needed!**

### For Teams:
- ✅ Teams webhook URL (from channel connector)
- ❌ **NO authentication needed!**

---

## 🎯 Next Steps

1. **Get your JIRA URL:**
   - Open a JIRA ticket
   - Copy the base URL

2. **Get your Teams webhook:**
   - Teams → Channel → Connectors → Incoming Webhook
   - Create and copy URL

3. **Test it:**
   ```bash
   gitdoctor delta \
     --base YOUR_BASE_TAG \
     --target YOUR_TARGET_TAG \
     -o test.html \
     --format html \
     --jira-url YOUR_JIRA_URL \
     --teams-webhook YOUR_TEAMS_WEBHOOK \
     -v
   ```

4. **Check results:**
   - Open `test.html` in browser
   - Check Teams channel for notification
   - Look for JIRA ticket links in the report

---

**Ready to test?** Just provide your JIRA URL and Teams webhook, and we can test it together! 🚀

