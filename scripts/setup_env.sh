#!/bin/bash
# Setup environment script

set -e

echo "=== Financial Risk Lakehouse Setup ==="
echo "Setting up development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

if ! command -v pip &> /dev/null; then
    echo "Error: pip not found"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found"
fi

# Install dev dependencies
echo "Installing development dependencies..."
pip install pytest pytest-cov black flake8 isort mypy

# Create local directories
echo "Creating data directories..."
mkdir -p data/{raw,bronze,silver,intermediate,gold,diamond}

# Copy env template
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your values"
fi

# Create .gitignore if doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore..."
    touch .gitignore
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Start services: docker-compose -f master/docker-compose.yml up -d"
echo "3. Initialize Airflow: cd master && ./startup.sh"
echo "4. Access Airflow at: http://localhost:8080"
echo ""
