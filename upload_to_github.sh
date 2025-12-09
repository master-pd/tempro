#!/bin/bash
# Upload all files to GitHub

echo "Uploading files to GitHub repository..."

# Add all files
git add .

# Commit with timestamp
COMMIT_MSG="Update: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG"

# Push to GitHub
git push origin main

echo "✅ All files uploaded to https://github.com/master-pd/tempro"
