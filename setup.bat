@echo off
echo ================================================
echo WebCV Backend - Automated Setup Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/7] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/7] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/7] Upgrading pip...
python -m pip install --upgrade pip

echo [4/7] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/7] Creating .env file from template...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please edit it with your database credentials!
) else (
    echo .env file already exists, skipping...
)

echo [6/7] Creating upload directories...
if not exist uploads\cvs mkdir uploads\cvs
if not exist uploads\profiles mkdir uploads\profiles

echo [7/7] Setup complete!
echo.
echo ================================================
echo Next Steps:
echo ================================================
echo 1. Edit .env file with your PostgreSQL password
echo 2. Create database: psql -U postgres -c "CREATE DATABASE webcv_db;"
echo 3. Run: flask db init
echo 4. Run: flask db migrate -m "Initial migration"
echo 5. Run: flask db upgrade
echo 6. Run: python seed.py
echo 7. Run: python run.py
echo ================================================
echo.
pause
