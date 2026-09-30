#!/bin/bash

# EduPredict Deployment Script
# This script helps deploy the app to GitHub and Streamlit Cloud

echo "🎓 EduPredict Pro - Deployment Helper"
echo "======================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Step 1: Initializing Git repository..."
    git init
    echo "✓ Git initialized"
else
    echo "✓ Git already initialized"
fi

echo ""
echo "📤 Step 2: Adding files to Git..."
git add .
echo "✓ Files added"

echo ""
echo "💾 Step 3: Committing changes..."
git commit -m "Initial commit: EduPredict Pro MVP with 3D visualizations and PDF reports"
echo "✓ Changes committed"

echo ""
echo "🔗 Step 4: Checking GitHub remote..."
if git remote | grep -q "origin"; then
    echo "✓ GitHub remote already configured"
else
    echo "⚠️  No GitHub remote found."
    echo ""
    echo "Please create a GitHub repository:"
    echo "1. Go to https://github.com/new"
    echo "2. Name it 'Edupredict' or 'EduPredict-Pro'"
    echo "3. Make it Public"
    echo "4. Do NOT initialize with README (we have one)"
    echo "5. Copy the repository URL"
    echo ""
    read -p "Paste your GitHub repository URL: " repo_url
    git remote add origin $repo_url
    echo "✓ Remote added"
fi

echo ""
echo "🚀 Step 5: Pushing to GitHub..."
git push -u origin main || git push -u origin master
echo "✓ Code pushed to GitHub"

echo ""
echo "======================================"
echo "🎉 Deployment Prep Complete!"
echo ""
echo "Next Steps:"
echo "1. Go to https://share.streamlit.io"
echo "2. Sign in with GitHub"
echo "3. Click 'New app'"
echo "4. Select your GitHub repo"
echo "5. Set main file path: ui/app.py"
echo "6. Click Deploy!"
echo ""
echo "Your app will be live at:"
echo "https://[your-app-name].streamlit.app"
echo ""
echo "Share this URL with your professor!"
echo "======================================"
