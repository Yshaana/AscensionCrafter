@echo off
rem =====================================================================
rem  AscensionCrafter HISTORICAL BACKFILL - run when you can leave the
rem  machine on for a few hours (overnight is ideal).
rem
rem  Unlike run_crawler.bat this is UNCAPPED: it walks report IDs upward
rem  until it hits 20 consecutive missing ones. Grind reports take ~10 min
rem  each, so a full backfill can run for several hours.
rem
rem  It is safe to interrupt with Ctrl+C. scan_log.json is saved after
rem  every report, so the next run resumes from where this one stopped -
rem  nothing is re-fetched and nothing is lost.
rem
rem  This is NOT the daily job. Use run_crawler.bat for that.
rem =====================================================================
setlocal
cd /d "%~dp0"

echo.
echo ==== Historical backfill (uncapped) - Ctrl+C is safe, progress is saved ====
echo.
py tools\scrapers\crawl_ascensionlogs.py
set CRAWL_EXIT=%ERRORLEVEL%

echo.
if "%CRAWL_EXIT%"=="0" (
    echo *********************************
    echo *  BACKFILL RUN: OK             *
    echo *********************************
) else (
    echo *****************************************************
    echo *  BACKFILL FINISHED WITH ERRORS - read the summary  *
    echo *****************************************************
)
pause
