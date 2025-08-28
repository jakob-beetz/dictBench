#!/bin/bash
# PropBench Development Environment Setup Script for Unix/macOS

# Set text colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python 3.11 is installed
PYTHON_VERSION=$(python3 --version 2>&1)
if [[ $PYTHON_VERSION != *"3.11"* ]]; then
    echo -e "${YELLOW}Warning: Python version is not 3.11. This project is designed to work with Python 3.11${NC}"
    echo -e "${YELLOW}Current version: $PYTHON_VERSION${NC}"
    read -p "Do you want to continue anyway? (y/n) " CONTINUE
    if [[ $CONTINUE != "y" ]]; then
        exit
    fi
else
    echo -e "${GREEN}Python 3.11 detected: $PYTHON_VERSION${NC}"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv-3.11" ]; then
    echo -e "${CYAN}Creating virtual environment...${NC}"
    python3 -m venv venv-3.11
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${CYAN}Activating virtual environment...${NC}"
source venv-3.11/bin/activate

# Install requirements
if [ -f "propbench/requirements.txt" ]; then
    echo -e "${CYAN}Installing dependencies...${NC}"
    pip install -r propbench/requirements.txt
else
    echo -e "${RED}requirements.txt not found in the propbench directory.${NC}"
    exit
fi

# Navigate to project directory
cd propbench

# Apply migrations
echo -e "${CYAN}Applying migrations...${NC}"
python manage.py migrate

# Check if superuser exists
SUPERUSER_EXISTS=$(python -c "
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
superusers = User.objects.filter(is_superuser=True)
print(superusers.exists())
")

if [ "$SUPERUSER_EXISTS" = "False" ]; then
    echo -e "${CYAN}No superuser found. Creating a superuser account...${NC}"
    python manage.py createsuperuser
else
    echo -e "${GREEN}Superuser already exists.${NC}"
fi

# Return to root directory
cd ..

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${CYAN}To start the development server, run:${NC}"
echo -e "${YELLOW}cd propbench${NC}"
echo -e "${YELLOW}python manage.py runserver${NC}"
