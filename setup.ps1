# setup.ps1
# PropBench Development Environment Setup Script for Windows

# Check if Python 3.11 is installed
try {
    $pythonVersion = python --version
    if (-not $pythonVersion.Contains("3.11")) {
        Write-Host "Warning: Python version is not 3.11. This project is designed to work with Python 3.11" -ForegroundColor Yellow
        Write-Host "Current version: $pythonVersion" -ForegroundColor Yellow
        $continue = Read-Host "Do you want to continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit
        }
    } else {
        Write-Host "Python 3.11 detected: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "Python not found. Please install Python 3.11 before continuing." -ForegroundColor Red
    exit
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path -Path "venv-3.11")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv-3.11
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv-3.11\Scripts\Activate.ps1

# Install requirements
if (Test-Path -Path "propbench\requirements.txt") {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    pip install -r propbench\requirements.txt
} else {
    Write-Host "requirements.txt not found in the propbench directory." -ForegroundColor Red
    exit
}

# Navigate to project directory
cd propbench

# Apply migrations
Write-Host "Applying migrations..." -ForegroundColor Cyan
python manage.py migrate

# Check if superuser exists
$checkSuperuser = python -c "
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propbench.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
superusers = User.objects.filter(is_superuser=True)
print(superusers.exists())
"

if ($checkSuperuser -eq "False") {
    Write-Host "No superuser found. Creating a superuser account..." -ForegroundColor Cyan
    python manage.py createsuperuser
} else {
    Write-Host "Superuser already exists." -ForegroundColor Green
}

# Return to root directory
cd ..

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To start the development server, run:" -ForegroundColor Cyan
Write-Host "cd propbench" -ForegroundColor Yellow
Write-Host "python manage.py runserver" -ForegroundColor Yellow
