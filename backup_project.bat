@echo off
:: ================================================================
::   DSR PRO AI - AUTOMATED PLATINUM BACKUP SYSTEM
::   Author: Gemini | Date: 2026-01-29
:: ================================================================
setlocal EnableDelayedExpansion

:: 1. CONFIGURATION
set "SOURCE_DIR=C:\Users\Bhanu\OneDrive\PROJECT\DSR_PRO_V2"
set "BACKUP_ROOT=C:\Users\Bhanu\OneDrive\PROJECT\DSR_BACKUPS"
set "TIMESTAMP=%date:~-4%-%date:~-7,2%-%date:~-10,2%_%time:~0,2%-%time:~3,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_NAME=DSR_PRO_Platinum_%TIMESTAMP%"
set "TARGET_DIR=%BACKUP_ROOT%\%BACKUP_NAME%"
set "ZIP_FILE=%BACKUP_ROOT%\%BACKUP_NAME%.zip"

echo [1/5] Initializing Backup Sequence...
echo       Source: %SOURCE_DIR%
echo       Target: %ZIP_FILE%

:: 2. CREATE BACKUP DIRECTORY
if not exist "%BACKUP_ROOT%" mkdir "%BACKUP_ROOT%"
mkdir "%TARGET_DIR%"

:: 3. GENERATE STATUS REPORT
echo [2/5] Generating Status Report...
(
    echo ========================================================
    echo  DSR PRO AI - PROJECT STATUS REPORT
    echo  Date Generated: %date% %time%
    echo ========================================================
    echo.
    echo [VERSION]: 1.1 - Platinum Edition (Frozen State)
    echo.
    echo [COMPLETED MODULES]
    echo  [x] UI: Obsidian Theme ^& Responsive 3x3 Grid
    echo  [x] UI: Zen Mode with Filmstrip
    echo  [x] UI: Executive Dashboard
    echo  [x] LOGIC: Dual-Mode Navigation (Grid/Zen)
    echo  [x] LOGIC: Filter Bar (All/Keep/Reject)
    echo  [x] LOGIC: Magic Analyze Button (Pulse)
    echo  [x] LOGIC: Lights Out Mode ('L')
    echo  [x] DATA: SQLite Database Integration
    echo.
    echo [KNOWN ISSUES]
    echo  - AI Engine is currently in Simulation Mode (Mock Data).
    echo.
    echo [PENDING FEATURES]
    echo  - Export Engine (Move files to final folder).
    echo  - Lazy Mode (Spacebar navigation).
    echo.
    echo ========================================================
    echo  Files Included in this Backup:
    echo   - main.py
    echo   - ui/ (gallery.py, dashboard.py, mainwindow.py)
    echo   - core/ (ai_engine.py, database.py)
    echo ========================================================
) > "%TARGET_DIR%\PROJECT_STATUS.txt"

:: 4. COPY SOURCE FILES
echo [3/5] Copying Codebase...
xcopy "%SOURCE_DIR%\main.py" "%TARGET_DIR%\" /Y /Q >nul
xcopy "%SOURCE_DIR%\ui\*" "%TARGET_DIR%\ui\" /S /I /Y /Q >nul
xcopy "%SOURCE_DIR%\core\*" "%TARGET_DIR%\core\" /S /I /Y /Q >nul

:: 5. COMPRESS TO ZIP (Using PowerShell)
echo [4/5] Compressing to ZIP...
powershell -command "Compress-Archive -Path '%TARGET_DIR%\*' -DestinationPath '%ZIP_FILE%'"

:: 6. CLEANUP
echo [5/5] Cleaning up temp files...
rmdir /S /Q "%TARGET_DIR%"

echo.
echo ========================================================
echo   BACKUP SUCCESSFUL!
echo   Location: %ZIP_FILE%
echo ========================================================
pause