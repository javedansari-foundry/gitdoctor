# Test JIRA & Teams Integration

Your configuration is now set up! Here's how to test it.

## ✅ Configuration Status

Your `config.yaml` now includes:
- ✅ **JIRA URL:** `https://comviva.atlassian.net`
- ✅ **JIRA Project Key:** `MON` (will extract MON-* tickets)
- ✅ **Teams Webhook:** Configured (Power Automate webhook)

## 🧪 Test Commands

### Test 1: Basic Delta with JIRA & Teams (from config)

```bash
cd /Users/comviva/GitDoctor/gitdoctor
source venv/bin/activate

# This will automatically use JIRA and Teams from config.yaml
gitdoctor delta \
  --base MobiquityPay_vX.10.15.2_PVG.B1 \
  --target MobiquityPay_v11.0.0_20250908_PVG.B1 \
  -o test-full-report.html \
  --format html \
  -v
```

**What this does:**
- ✅ Uses JIRA URL from config (`https://comviva.atlassian.net`)
- ✅ Extracts MON-* tickets from commits
- ✅ Sends notification to Teams
- ✅ Generates HTML report with JIRA links

### Test 2: CSV with JIRA (from config)

```bash
# Generate CSV with JIRA ticket columns
gitdoctor delta \
  --base MobiquityPay_vX.10.15.2_PVG.B1 \
  --target MobiquityPay_v11.0.0_20250908_PVG.B1 \
  -o test-with-jira.csv \
  -v
```

**Check the CSV:**
```bash
# View the CSV
head -5 test-with-jira.csv

# Check for JIRA tickets column
cat test-with-jira.csv | cut -d',' -f21 | head -10
```

### Test 3: Override Config (use different JIRA project)

```bash
# Override project key from command line
gitdoctor delta \
  --base MobiquityPay_vX.10.15.2_PVG.B1 \
  --target MobiquityPay_v11.0.0_20250908_PVG.B1 \
  -o test.csv \
  --jira-project JIRA \
  -v
```

This will use JIRA URL from config but override project key to extract JIRA-* tickets instead.

## 📊 What to Expect

### In the Output:

1. **JIRA Integration Message:**
   ```
   JIRA integration enabled - extracting ticket references
     Using JIRA URL from config: https://comviva.atlassian.net
     Using JIRA project key from config: MON
   ```

2. **JIRA Tickets Summary:**
   ```
   ============================================================
   JIRA Tickets Found
   ============================================================
   MON-12345: 5 commit(s) in 3 project(s)
     URL: https://comviva.atlassian.net/browse/MON-12345
   MON-12346: 2 commit(s) in 1 project(s)
     URL: https://comviva.atlassian.net/browse/MON-12346
   ============================================================
   ```

3. **Teams Notification:**
   ```
   Sending Teams notification...
     Using Teams webhook from config
   Teams notification sent successfully
   ```

### In HTML Report:

- Clickable JIRA ticket badges in commits table
- Dedicated "JIRA Tickets" section
- All MON-* tickets linked to `https://comviva.atlassian.net/browse/MON-XXXXX`

### In CSV:

- `jira_tickets` column: Pipe-separated ticket IDs (e.g., `MON-12345|MON-12346`)
- `jira_ticket_urls` column: Pipe-separated URLs

### In Teams Channel:

- Message card with summary statistics
- Color-coded (green=success, red=errors)
- Link to generated report file

## 🔍 Verify It's Working

### Check 1: JIRA Links Work

After running, open the HTML report and click on any JIRA ticket badge. It should open:
```
https://comviva.atlassian.net/browse/MON-XXXXX
```

### Check 2: Teams Notification

Check your Teams channel - you should see a message card with:
- 🔍 GitDoctor Delta Discovery Complete
- Summary statistics
- Report file name

### Check 3: CSV Has JIRA Columns

```bash
# Check CSV headers
head -1 test-with-jira.csv | tr ',' '\n' | grep -n jira

# Should show:
# 21:jira_tickets
# 22:jira_ticket_urls
```

## 🎯 Quick Test (One Command)

```bash
gitdoctor delta \
  --base MobiquityPay_vX.10.15.2_PVG.B1 \
  --target MobiquityPay_v11.0.0_20250908_PVG.B1 \
  -o quick-test.html \
  --format html \
  -v
```

This single command will:
1. ✅ Load JIRA config from `config.yaml`
2. ✅ Load Teams webhook from `config.yaml`
3. ✅ Extract MON-* tickets
4. ✅ Generate HTML report
5. ✅ Send Teams notification
6. ✅ Show summary

**No need to pass `--jira-url` or `--teams-webhook` - it's all in config!** 🎉

## 📝 Configuration Location

All settings are in: `/Users/comviva/GitDoctor/gitdoctor/config.yaml`

**JIRA Section:**
```yaml
jira:
  base_url: "https://comviva.atlassian.net"
  project_key: "MON"
```

**Teams Section:**
```yaml
notifications:
  teams_webhook: "https://default84ee5792e85e4bbea9d61b06a2157e..."
```

## 🚀 Ready to Test!

Run the quick test command above and check:
1. HTML report opens with JIRA links
2. Teams channel receives notification
3. Summary shows JIRA tickets found

Let me know the results! 🎯

