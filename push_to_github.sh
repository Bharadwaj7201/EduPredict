#!/bin/bash

echo "🎓 EduPredict Pro - Pushing to GitHub"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "ui/app.py" ]; then
    echo "❌ Error: ui/app.py not found!"
    echo "Please run this script from the EduPredict-MVP directory"
    exit 1
fi

echo "📦 Step 1: Initializing Git..."
git init
echo "✓ Git initialized"

echo ""
echo "🔗 Step 2: Adding GitHub remote..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/GaneshMunagala714/Edupredict.git
echo "✓ Remote added"

echo ""
echo "📤 Step 3: Adding files..."
git add .
echo "✓ Files added"

echo ""
echo "💾 Step 4: Committing..."
git commit -m "Complete rebuild: Professional Streamlit dashboard with 3D visualizations, PDF reports, and ROI analysis"
echo "✓ Committed"

echo ""
echo "🚀 Step 5: Pushing to GitHub (replacing old files)..."
git push -f origin main
echo "✓ Pushed to GitHub"

echo ""
echo "======================================"
echo "🎉 Success! Your code is on GitHub!"
echo ""
echo "Next Step: Deploy to Streamlit Cloud"
echo "1. Go to https://share.streamlit.io"
echo "2. Sign in with GitHub"
echo "3. Click 'New app'"
echo "4. Select: GaneshMunagala714/Edupredict"
echo "5. Main file: ui/app.py"
echo "6. Click Deploy!"
echo ""
echo "======================================"
