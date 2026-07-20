#!/usr/bin/env bash
# daily-brief.sh — Generate today's Brief and push to GitHub
# Designed for cron: 0 7 * * * /home/aeon/.openclaw/workspace/aeonos/projects/brief-landing/daily-brief.sh
set -euo pipefail

REPO_DIR="/home/aeon/.openclaw/workspace/aeonos/projects/brief-landing"
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
cd "$REPO_DIR"

# Generate today's digest
TODAY=$(date -u +%Y-%m-%d)
python3 brief.py content/today.md 2>>"$REPO_DIR/output/brief.log"

# Archive: copy today's edition to posts/ for historical permalink
mkdir -p content/posts
cp content/today.md "content/posts/${TODAY}.md"

# Build the site
hugo build --minify 2>>"$REPO_DIR/output/brief.log"

# Commit and push
git add content/today.md content/posts/
if git diff --cached --quiet; then
    echo "$(date -u +%Y-%m-%dT%H:%M): No changes to commit" >> "$REPO_DIR/output/brief.log"
else
    git commit -m "feat: Brief ${TODAY} — daily auto-update"
    git push origin main 2>>"$REPO_DIR/output/brief.log"
    echo "$(date -u +%Y-%m-%dT%H:%M): Pushed Brief for ${TODAY}" >> "$REPO_DIR/output/brief.log"
fi
