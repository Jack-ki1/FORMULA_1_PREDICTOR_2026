@echo off
echo ============================================================
echo F1 Predictor 2026 - Quick Deployment Helper
echo ============================================================
echo.

echo This script helps you deploy to Hugging Face Spaces
echo.
echo Prerequisites:
echo   1. Git installed
echo   2. Hugging Face account (free at huggingface.co)
echo   3. All project files in this directory
echo.
pause

echo.
echo Step 1: Checking for required files...
echo ------------------------------------------------------------

if not exist "dashboard\app.py" (
    echo ERROR: dashboard\app.py not found!
    echo Make sure you're running this from the project root.
    pause
    exit /b 1
)

if not exist "Dockerfile" (
    echo ERROR: Dockerfile not found!
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
)

echo [OK] All required files present
echo.

echo Step 2: Initialize Git repository...
echo ------------------------------------------------------------

if not exist ".git" (
    echo Initializing Git repository...
    git init
    git add .
    git commit -m "Initial commit for Hugging Face deployment"
    echo [OK] Git repository initialized
) else (
    echo [OK] Git repository already exists
)

echo.

echo Step 3: Test locally with Docker (optional)...
echo ------------------------------------------------------------
set /p TEST_DOCKER="Do you want to test locally with Docker first? (y/n): "

if /i "%TEST_DOCKER%"=="y" (
    echo Building Docker image...
    docker build -t f1-predictor-test .
    
    if errorlevel 1 (
        echo ERROR: Docker build failed!
        echo Check the error messages above.
        pause
        exit /b 1
    )
    
    echo.
    echo Starting local test server...
    echo Visit http://localhost:7860 in your browser
    echo Press Ctrl+C to stop the test server
    echo.
    docker run -p 7860:7860 f1-predictor-test
    
    echo.
    set /p CONTINUE="Continue with deployment? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo Deployment cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Step 4: Prepare for Hugging Face upload...
echo ------------------------------------------------------------

echo Your next steps:
echo.
echo 1. Create a Hugging Face Space:
echo    - Go to: https://huggingface.co/new-space
echo    - Name: f1-predictor-2026
echo    - SDK: Docker
echo    - Click "Create Space"
echo.
echo 2. Copy your Space's Git URL from the page
echo.
echo 3. Run these commands:
echo    git remote add origin YOUR_SPACE_URL
echo    git push -u origin main
echo.
echo 4. Wait 5-10 minutes for build
echo.
echo 5. Visit: https://YOUR_USERNAME-f1-predictor-2026.hf.space
echo.

echo ============================================================
echo For detailed instructions, see DEPLOYMENT_GUIDE.md
echo ============================================================
echo.
pause
