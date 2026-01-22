#!/bin/bash
# Push to both GitHub (public, sanitized) and Comviva GitLab (internal, full info)

set -e

echo "🚀 Pushing to both repositories..."
echo ""

# Check current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"
echo ""

# Push to GitHub (public repo with sanitized docs)
echo "📤 1. Pushing to GitHub (public)..."
git push origin $BRANCH
echo "   ✅ Pushed to: https://github.com/javedansari-foundry/gitdoctor"
echo ""

# Push to Comviva GitLab (internal repo with full info)
echo "📤 2. Pushing to Comviva GitLab (internal)..."
git push comviva $BRANCH
echo "   ✅ Pushed to: http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor"
echo ""

echo "✅ All done! Both repositories are now in sync."
echo ""
echo "📍 Repositories:"
echo "   Public:   https://github.com/javedansari-foundry/gitdoctor (sanitized)"
echo "   Internal: http://blrgitlab.comviva.com/dfs-core/automation/gitdoctor (full)"

