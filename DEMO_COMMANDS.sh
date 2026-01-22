#!/bin/bash
# GitDoctor Demo Commands
# Copy-paste these commands during your recording session
# Usage: Source this file or copy individual commands

# =============================================================================
# DEMO: Delta Discovery Between Two Tags
# =============================================================================

# Tags for this demo
BASE_TAG="MobiquityPay_vX.10.15.8_L4Patch_19Jan26"
TARGET_TAG="MobiquityPay_vX.10.15.8_PVG.B1"

echo "==================================================================="
echo "GitDoctor Demo - Delta Discovery"
echo "==================================================================="
echo "Base Tag:   $BASE_TAG"
echo "Target Tag: $TARGET_TAG"
echo "==================================================================="
echo ""

# -----------------------------------------------------------------------------
# 1. SETUP - Verify Installation
# -----------------------------------------------------------------------------
echo "Step 1: Verify Installation"
echo "Command: gitdoctor --version"
echo ""

cd /Users/javedansari/My\ Projects/GitDoctor/gitdoctor
source venv/bin/activate
gitdoctor --version

echo ""
echo "✅ GitDoctor is installed"
echo ""
read -p "Press Enter to continue..."

# -----------------------------------------------------------------------------
# 2. SHOW CONFIGURATION (sanitized)
# -----------------------------------------------------------------------------
echo ""
echo "Step 2: Show Configuration"
echo "Command: cat config.yaml | grep -A 5 '^gitlab:' | grep -v 'private_token'"
echo ""

cat config.yaml | grep -A 5 "^gitlab:" | grep -v "private_token"

echo ""
echo "✅ Connected to: http://blrgitlab.comviva.com"
echo ""
read -p "Press Enter to continue..."

# -----------------------------------------------------------------------------
# 3. RUN DELTA DISCOVERY - HTML Format
# -----------------------------------------------------------------------------
echo ""
echo "Step 3: Run Delta Discovery (HTML Report)"
echo "Command:"
echo "  gitdoctor delta \\"
echo "    --base $BASE_TAG \\"
echo "    --target $TARGET_TAG \\"
echo "    --format html \\"
echo "    -o delta-report.html \\"
echo "    -v"
echo ""
read -p "Press Enter to run..."

gitdoctor delta \
  --base "$BASE_TAG" \
  --target "$TARGET_TAG" \
  --format html \
  -o delta-report.html \
  -v

echo ""
echo "✅ HTML report generated: delta-report.html"
echo ""
read -p "Press Enter to continue..."

# -----------------------------------------------------------------------------
# 4. OPEN HTML REPORT
# -----------------------------------------------------------------------------
echo ""
echo "Step 4: Open HTML Report in Browser"
echo "Command: open delta-report.html"
echo ""
read -p "Press Enter to open..."

open delta-report.html

echo "✅ Report opened in browser"
echo ""
read -p "Press Enter to continue..."

# -----------------------------------------------------------------------------
# 5. EXPORT AS CSV
# -----------------------------------------------------------------------------
echo ""
echo "Step 5: Export as CSV for Analysis"
echo "Command:"
echo "  gitdoctor delta \\"
echo "    --base $BASE_TAG \\"
echo "    --target $TARGET_TAG \\"
echo "    --format csv \\"
echo "    -o delta-report.csv"
echo ""
read -p "Press Enter to run..."

gitdoctor delta \
  --base "$BASE_TAG" \
  --target "$TARGET_TAG" \
  --format csv \
  -o delta-report.csv

echo ""
echo "✅ CSV report generated: delta-report.csv"
echo ""

# Show first few lines
echo "Preview (first 10 lines):"
head -10 delta-report.csv

echo ""
read -p "Press Enter to continue..."

# -----------------------------------------------------------------------------
# 6. BONUS: MR CHANGES FOR TEST SELECTION
# -----------------------------------------------------------------------------
echo ""
echo "Step 6: BONUS - Get MR Changes for Test Selection"
echo "This shows file-level changes for intelligent test selection"
echo ""
echo "Command:"
echo "  gitdoctor mr-changes \\"
echo "    --project 127 \\"
echo "    --mr <MR_NUMBER> \\"
echo "    --format test-selection \\"
echo "    -o mr-changes.json"
echo ""
echo "(Skipping in this demo - requires specific MR number)"
echo ""

# Uncomment if you have a real MR to demo:
# gitdoctor mr-changes \
#   --project 127 \
#   --mr 123 \
#   --format test-selection \
#   -o mr-changes.json

# -----------------------------------------------------------------------------
# 7. SUMMARY
# -----------------------------------------------------------------------------
echo ""
echo "==================================================================="
echo "Demo Complete! ✅"
echo "==================================================================="
echo ""
echo "Generated Files:"
echo "  - delta-report.html    (Visual report with JIRA links)"
echo "  - delta-report.csv     (Spreadsheet format)"
echo ""
echo "Documentation:"
echo "  - TEAM_QUICKSTART.md   (Quick start guide)"
echo "  - README.md            (Complete documentation)"
echo "  - DELTA_GUIDE.md       (Delta discovery guide)"
echo "  - MR_CHANGES_GUIDE.md  (Test selection guide)"
echo ""
echo "Repository: https://github.com/javedansari-foundry/gitdoctor"
echo "==================================================================="
echo ""

