#!/bin/bash
# EduPredict MVP - Run Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  EduPredict MVP - Launch Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Run the app
echo ""
echo -e "${GREEN}Starting EduPredict MVP...${NC}"
echo -e "${BLUE}Open your browser at: http://localhost:8501${NC}"
echo ""

streamlit run ui/app.py

# Deactivate on exit
deactivate