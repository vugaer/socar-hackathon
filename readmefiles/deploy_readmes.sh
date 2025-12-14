#!/bin/bash

###############################################################################
# Deploy README files to Drillica repository and push to Git
# Team Drillica - SOCAR Hackathon 2024
###############################################################################

set -e  # Exit on error

echo "======================================================================"
echo "DRILLICA README DEPLOYMENT SCRIPT"
echo "Team Drillica - SOCAR Hackathon 2024"
echo "======================================================================"
echo ""

# Check if all_readme_files.csv exists
if [ ! -f "all_readme_files.csv" ]; then
    echo "❌ Error: all_readme_files.csv not found!"
    echo "   Please run this script from the directory containing all_readme_files.csv"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found!"
    echo "   Please install Python 3"
    exit 1
fi

# Use the Python deployment script
if [ -f "deploy_readmes.py" ]; then
    echo "Using Python deployment script..."
    chmod +x deploy_readmes.py
    python3 deploy_readmes.py
else
    echo "❌ Error: deploy_readmes.py not found!"
    echo "   Please ensure deploy_readmes.py is in the same directory"
    exit 1
fi
