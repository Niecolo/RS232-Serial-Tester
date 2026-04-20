@echo off
@CHCP 65001 >nul
setlocal enabledelayedexpansion

REM ==================================================
REM Serial Port Tester - Portable Build Script for Windows
REM ==================================================
REM This script creates a completely portable standalone EXE
REM with all dependencies included, no installation required.
REM ==================================================

echo.
echo ==============================================
echo  Serial Port Tester Portable Build Script
echo ==============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [+] Checking required packages...

REM Install/upgrade required packages
pip install --upgrade pip >nul
pip install pyserial pyinstaller >nul

if not exist "RS232.ico" (
    echo WARNING: RS232.ico not found, will use default icon
)

echo.
echo [+] Starting PyInstaller build process...
echo.

REM Clean previous builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "Serial Port Tester.spec" del /f "Serial Port Tester.spec"

REM Build completely standalone portable executable
pyinstaller --onefile ^
            --windowed ^
            --noconsole ^
            --icon="RS232.ico" ^
            --name="Serial Port Tester" ^
            --add-data="RS232.ico;." ^
            --exclude-module=test ^
            --exclude-module=distutils ^
            --hidden-import=tkinter ^
            --hidden-import=tkinter.ttk ^
            --clean ^
            serial_transmitter.py

echo.
if exist "dist\Serial Port Tester.exe" (
    echo ==============================================
    echo  BUILD SUCCESSFUL!
    echo ==============================================
    echo.
    echo Portable executable created at:
    echo   %cd%\dist\Serial Port Tester.exe
    echo.
    echo Features:
    echo  ✓ Completely standalone - no Python required
    echo  ✓ All dependencies embedded inside EXE
    echo  ✓ Icon properly included
    echo  ✓ Portable - runs from any folder/USB drive
    echo  ✓ No installation required
    echo  ✓ Single file distribution
    echo.
    echo File size: ~8-12 MB
    echo.

    REM Open output folder
    explorer dist
) else (
    echo ==============================================
    echo  BUILD FAILED
    echo ==============================================
    echo Check PyInstaller output above for errors
    pause
    exit /b 1
)

echo.
pause