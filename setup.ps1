#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup script for Register Machine development environment (Windows).

.DESCRIPTION
    Creates a virtual environment, installs dependencies, and verifies setup.

.EXAMPLE
    .\setup.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🔧 Setting up Register Machine development environment..." -ForegroundColor Cyan
Write-Host ""

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10 or later." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "✓ Virtual environment created at .venv/" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "✨ Activating environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Upgrade pip and build tools
Write-Host "📥 Upgrading pip, setuptools, and wheel..." -ForegroundColor Cyan
python -m pip install --upgrade pip setuptools wheel
Write-Host "✓ Build tools upgraded" -ForegroundColor Green
Write-Host ""

# Install project in editable mode
Write-Host "📚 Installing project and dependencies..." -ForegroundColor Cyan
pip install -e .
Write-Host "✓ Project installed in editable mode" -ForegroundColor Green

pip install -r backend/requirements.txt
Write-Host "✓ Backend dependencies installed" -ForegroundColor Green

pip install pytest pytest-cov
Write-Host "✓ Testing dependencies installed" -ForegroundColor Green
Write-Host ""

# Verify installation
Write-Host "🧪 Verifying installation..." -ForegroundColor Cyan
python -c "import register_machine; print('✓ register_machine imports successfully')"
Write-Host ""

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment for future sessions, run:" -ForegroundColor Yellow
Write-Host "  .\\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Yellow
Write-Host "  pytest src/register_machine/tests/" -ForegroundColor White
Write-Host "  pytest backend/tests/" -ForegroundColor White
Write-Host ""
Write-Host "To start the backend:" -ForegroundColor Yellow
Write-Host "  cd backend && python -m uvicorn api:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "To start with Docker Compose:" -ForegroundColor Yellow
Write-Host "  docker compose up" -ForegroundColor White
Write-Host ""
