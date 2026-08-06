#!/bin/bash
# Sanitize repository - Remove Comviva-specific information for public GitHub

echo "🧹 Sanitizing repository..."
echo "Removing company-specific information from documentation"
echo ""

# Files to sanitize
FILES=(
    "config.example.yaml"
    "DEMO_COMMANDS.sh"
    "DEMO_COMMANDS_QUICK.txt"
    "DEMO_SCRIPT.md"
    "MR_CHANGES_GUIDE.md"
    "TEAM_QUICKSTART.md"
    "README.md"
)

# Replacements
declare -A replacements=(
    ["blrgitlab.comviva.com"]="gitlab.example.com"
    ["comviva.atlassian.net"]="jira.company.com"
    ["dfs-core"]="your-org"
    ["Comviva"]="Company"
    ["comviva"]="company"
)

# Perform replacements
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📄 Sanitizing: $file"
        for search in "${!replacements[@]}"; do
            replace="${replacements[$search]}"
            # Use sed with backup
            sed -i.bak "s|$search|$replace|g" "$file"
        done
        # Remove backup files
        rm -f "${file}.bak"
    else
        echo "⚠️  File not found: $file"
    fi
done

echo ""
echo "✅ Sanitization complete!"
echo "🔍 Verify changes with: git diff"
echo "📤 Push to GitHub with: git add . && git commit -m 'docs: sanitize company-specific information' && git push origin main"

