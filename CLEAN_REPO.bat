@echo off
echo F1MLpredictions2026 - Repository Preparation Tool
echo ============================================================

echo Starting repository cleanup...

REM Remove __pycache__ directories
echo Removing __pycache__ directories...
for /d /r %%i in (__pycache__) do @if exist "%%i" rd /s /q "%%i"

REM Remove specific files that should not be in the repository
if exist output_test.json (
    echo Removing output_test.json...
    del output_test.json
)

REM Create a directory listing to verify the current state
echo.
echo Current repository structure:
echo =============================
dir /s /b

echo.
echo Repository cleanup completed!
echo.
echo Next steps:
echo 1. Review the GITHUB_PREPARATION.md file for complete instructions
echo 2. Make sure to add a LICENSE file if you want to license the code  
echo 3. Verify all sensitive information is properly excluded via .gitignore
echo 4. Commit and push to your GitHub repository
echo.

pause