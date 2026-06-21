#!/bin/bash
set -e

echo "🔧 Setting up Register Machine development environment..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

echo "✓ Virtual environment created at .venv/"
echo ""

# Activate and upgrade pip
echo "📥 Activating environment and upgrading pip..."
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
echo "✓ pip upgraded"
echo ""

# Install project and dependencies
echo "📚 Installing project and dependencies..."
pip install -e .
echo "✓ Project installed in editable mode"

pip install -r backend/requirements.txt
echo "✓ Backend dependencies installed"

pip install pytest pytest-cov
echo "✓ Testing dependencies installed"
echo ""

# Verify installation
echo "🧪 Verifying installation..."
python -c "import register_machine; print('✓ register_machine imports successfully')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest src/register_machine/tests/"
echo "  pytest backend/tests/"
echo ""
echo "To start the backend:"
echo "  cd backend && python -m uvicorn api:app --reload"
echo ""
echo "To start with Docker Compose:"
echo "  docker compose up"
