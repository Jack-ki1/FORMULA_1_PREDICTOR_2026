@echo off
echo ============================================================
echo F1 Predictor v3.0 - Cleanup and Test Script
echo ============================================================
echo.

echo Step 1: Deleting Git files and directories...
echo ------------------------------------------------------------
if exist .git (
    echo Deleting .git directory...
    rmdir /S /Q .git
    echo .git directory deleted.
) else (
    echo .git directory not found or already deleted.
)

if exist .gitignore (
    echo Deleting .gitignore...
    del /Q .gitignore
    echo .gitignore deleted.
) else (
    echo .gitignore not found or already deleted.
)

if exist .github (
    echo Deleting .github directory...
    rmdir /S /Q .github
    echo .github directory deleted.
) else (
    echo .github directory not found.
)

echo.
echo Step 2: Verifying reports folder exists...
echo ------------------------------------------------------------
if exist reports\html_report.py (
    echo ✅ Reports folder exists with html_report.py
) else (
    echo ❌ Reports folder missing! Please check.
)

echo.
echo Step 3: Installing dependencies (if needed)...
echo ------------------------------------------------------------
pip install -q -r requirements.txt
echo Dependencies installed.

echo.
echo Step 4: Running comprehensive tests...
echo ------------------------------------------------------------
py test_v3_complete.py

echo.
echo ============================================================
echo Cleanup and Testing Complete!
echo ============================================================
echo.
echo If all tests passed, your project is ready!
echo.
echo Next commands to try:
echo   py main.py migrate-db
echo   py main.py predict --race canada --sims 10000 --store
echo   py main.py h2h --driver1 verstappen --driver2 hamilton --race canada
echo   py main.py dashboard
echo.
pause
