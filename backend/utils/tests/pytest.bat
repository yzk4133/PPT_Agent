@echo off
REM Pytest wrapper for Windows users
REM Usage: pytest.bat [options]

echo Running pytest for backend/utils tests...
echo.

cd %~dp0
python -m pytest %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Tests completed successfully!
) else (
    echo.
    echo Tests failed with error code %ERRORLEVEL%
)

pause
