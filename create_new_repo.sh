#!/bin/bash

echo "🎓 EduPredict Pro - Creating New GitHub Repo"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "ui/app.py" ]; then
    echo "❌ Error: ui/app.py not found!"
    echo "Please run this script from the EduPredict-MVP directory"
    exit 1
fi

echo "⚠️  IMPORTANT: Create a new GitHub repository first!"
echo ""
echo "Steps:"
echo "1. Go to https://github.com/new"
echo "2. Repository name: Edupredict-Pro (or any name you want)"
echo "3. Description: Professional Streamlit dashboard for AI degree planning"
echo "4. Make it Public"
echo "5. DO NOT initialize with README (we have one)"
echo "6. Click 'Create repository'"
echo "7. Copy the repository URL"
echo ""

read -p "Paste your NEW GitHub repository URL: " repo_url

echo ""
echo "📦 Initializing Git..."
git init
echo "✓ Git initialized"

echo ""
echo "🔗 Adding new GitHub remote..."
git remote add origin $repo_url
echo "✓ Remote added: $repo_url"

echo ""
echo "📤 Adding files..."
git add .
echo "✓ Files added"

echo ""
echo "💾 Committing..."
git commit -m "EduPredict Pro: Professional Streamlit dashboard with 3D visualizations, PDF reports, and ROI analysis"
echo "✓ Committed"

echo ""
echo "🚀 Pushing to new GitHub repo..."
git push -u origin main
echo "✓ Pushed to GitHub"

echo ""
echo "======================================"
echo "🎉 Success! New repo created!"
echo ""
echo "Your old dashboard stays at:"
echo "https://github.com/GaneshMunagala714/Edupredict"
echo ""
echo "Your new Streamlit app is at:"
echo "$repo_url"
echo ""
echo "Next Step: Deploy to Streamlit Cloud"
echo "1. Go to https://share.streamlit.io"
echo "2. Sign in with GitHub"
echo "3. Click 'New app'"
echo "4. Select your NEW repo"
echo "5. Main file: ui/app.py"
echo "6. Click Deploy!"
echo ""
echo "======================================"
