@echo off
rem =====================================================================
rem  AscensionCrafter daily capture — double-click to run (Phase 0 Task 6)
rem  1. Snapshots the changelog (also refreshes the patch-date stamp)
rem  2. Crawls darkmoon.ascensionlogs.gg (reports, leaderboards, armories)
rem  3. The crawler auto-commits and pushes data/source at the end
rem  Manual-first: no scheduler. Run this once a day, watch the summary.
rem =====================================================================
setlocal
cd /d "%~dp0"

echo.
echo ==== [1/2] Changelog snapshot ====
py tools\scrapers\fetch_changelog.py
if errorlevel 1 echo [WARN] changelog fetcher reported a problem - see above.

echo.
echo ==== [2/2] ascensionlogs crawl ====
py tools\scrapers\crawl_ascensionlogs.py
set CRAWL_EXIT=%ERRORLEVEL%

echo.
if "%CRAWL_EXIT%"=="0" (
    echo *********************************
    echo *  DAILY CAPTURE: OK            *
    echo *********************************
) else (
    echo *********************************************************
    echo *  DAILY CAPTURE FINISHED WITH ERRORS - read the summary *
    echo *********************************************************
)
pause
