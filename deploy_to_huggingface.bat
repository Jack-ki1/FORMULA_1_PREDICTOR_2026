@echo off
setlocal enabledelayedexpansion
title F1 Predictor 2026 - Hugging Face Deployment Helper
echo ============================================================
echo   F1 Predictor 2026 - Hugging Face Space Deployment Helper
echo ============================================================
echo.

REM ------------------------------------------------------------
REM Step 1: Verify required files exist
REM ------------------------------------------------------------
echo [1/4] Checking required files...
set MISSING=0

call :check_file "Dockerfile"
call :check_file "requirements.txt"
call :check_file "main.py"
call :check_file "dashboard\app.py"
call :check_file "README.md"

if "%MISSING%"=="1" (
    echo.
    echo   One or more required files are missing. Fix before continuing.
    pause
    exit /b 1
)
echo   All required files found.
echo.

REM ------------------------------------------------------------
REM Step 2: Initialize git repository if needed
REM ------------------------------------------------------------
echo [2/4] Checking git repository...
if not exist ".git" (
    echo   No git repository found. Initializing...
    git init
    git add .
    git commit -m "Initial commit for Hugging Face deployment"
) else (
    echo   Git repository already initialized.
)
echo.

REM ------------------------------------------------------------
REM Step 3: Optional local Docker test
REM ------------------------------------------------------------
echo [3/4] Local Docker test (optional)
set /p RUN_DOCKER="Build and test the Docker image locally first? (y/n): "
if /i "%RUN_DOCKER%"=="y" (
    where docker >nul 2>nul
    if errorlevel 1 (
        echo   Docker not found on PATH. Skipping local test.
    ) else (
        echo   Building image "f1-predictor-2026-test"...
        docker build -t f1-predictor-2026-test .
        if errorlevel 1 (
            echo   Docker build failed - fix the errors above before deploying.
            pause
            exit /b 1
        )
        echo   Starting container on http://localhost:7860
        echo   Press Ctrl+C in this window to stop the test container.
        docker run --rm -p 7860:7860 -e FLASK_PORT=7860 f1-predictor-2026-test
    )
)
echo.

REM ------------------------------------------------------------
REM Step 4: Guide through Hugging Face Space setup
REM ------------------------------------------------------------
echo [4/4] Hugging Face Space setup
echo.
echo   1. Go to https://huggingface.co/new-space
echo   2. Space name:  f1-predictor-2026
echo   3. SDK:         Docker
echo   4. Click "Create Space"
echo.
set /p HF_USER="Enter your Hugging Face username: "
set /p HF_SPACE="Enter your Space name [f1-predictor-2026]: "
if "%HF_SPACE%"=="" set HF_SPACE=f1-predictor-2026

set HF_URL=https://huggingface.co/spaces/%HF_USER%/%HF_SPACE%
echo.
echo   Space URL will be: %HF_URL%
echo.
set /p CONFIRM="Add this as git remote 'origin' and push now? (y/n): "
if /i "%CONFIRM%"=="y" (
    git remote remove origin >nul 2>nul
    git remote add origin %HF_URL%
    git branch -M main
    git push -u origin main
    echo.
    echo   Done. Your Space will build for 5-10 minutes at:
    echo   https://%HF_USER%-%HF_SPACE%.hf.space
) else (
    echo.
    echo   Skipped push. When ready, run manually:
    echo     git remote add origin %HF_URL%
    echo     git push -u origin main
)

echo.
echo ============================================================
echo   Deployment helper finished.
echo ============================================================
pause
exit /b 0

:check_file
if not exist %1 (
    echo   [MISSING] %~1
    set MISSING=1
) else (
    echo   [OK] %~1
)
exit /b 0