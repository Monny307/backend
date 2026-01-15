#!/bin/bash

echo "================================================"
echo "WebCV Backend - Automated Setup Script"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "[1/7] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/7] Activating virtual environment..."
source venv/bin/activate

echo "[3/7] Upgrading pip..."
python -m pip install --upgrade pip

echo "[4/7] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[5/7] Creating .env file from template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created. Please edit it with your database credentials!"
else
    echo ".env file already exists, skipping..."
fi

echo "[6/7] Creating upload directories..."
mkdir -p uploads/cvs
mkdir -p uploads/profiles

echo "[7/7] Setup complete!"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo "1. Edit .env file with your PostgreSQL password"
echo "2. Create database: sudo -u postgres psql -c 'CREATE DATABASE webcv_db;'"
echo "3. Run: flask db init"
echo "4. Run: flask db migrate -m 'Initial migration'"
echo "5. Run: flask db upgrade"
echo "6. Run: python seed.py"
echo "7. Run: python run.py"
echo "================================================"
echo ""
