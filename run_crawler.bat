@echo off
rem =====================================================================
rem  AscensionCrafter DAILY capture - double-click to run (Phase 0 Task 6)
rem
rem  1. Snapshots the changelog (also refreshes the patch-date stamp)
rem  2. Crawls darkmoon.ascensionlogs.gg, capped at 25 new reports so a
rem     daily run stays bounded and predictable (~30-60 min worst case)
rem  3. Auto-commits and pushes data/source at the end
rem
rem  For the long historical backfill, use catchup_crawler.bat instead -
rem  that one is uncapped and can run for hours.
rem
rem  Manual-first: no scheduler. Run once a day, read the summary.
rem =====================================================================
setlocal
cd /d "%~dp0"

echo.
echo ==== [1/2] Changelog snapshot ====
py tools\scrapers\fetch_changelog.py
if errorlevel 1 echo [WARN] changelog fetcher reported a problem - see above.

echo.
echo ==== [2/2] ascensionlogs crawl (max 25 new reports) ====
py tools\scrapers\crawl_ascensionlogs.py --max-reports 25
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
