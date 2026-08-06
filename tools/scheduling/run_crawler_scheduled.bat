@echo off
rem =====================================================================
rem  AscensionCrafter DAILY capture - the SCHEDULED entry point.
rem
rem  Two differences from run_crawler.bat, and both matter:
rem
rem   1. NO `pause` at the end. Task Scheduler has no one to press a key,
rem      so a pause would hang the task until the 2-hour limit killed it.
rem   2. A once-per-day guard. The trigger is "at logon", and logging on
rem      more than once a day is normal, so this exits early if today's
rem      capture already succeeded.
rem
rem  Double-clicking run_crawler.bat still works and deliberately IGNORES
rem  the guard - a manual run is an explicit act and should always run.
rem
rem  Registered by register_daily_crawler.ps1. See SCHEDULING.md.
rem =====================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0..\.."

for /f %%d in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd\")"') do set TODAY=%%d
set STAMP=data\derived\last_scheduled_crawl.txt

if exist "%STAMP%" (
    set /p LASTRUN=<"%STAMP%"
    if "!LASTRUN!"=="!TODAY!" (
        echo [skip] Today's capture ^(!TODAY!^) already ran successfully. Nothing to do.
        exit /b 0
    )
)

echo.
echo ==== [1/2] Changelog snapshot ====
py tools\scrapers\fetch_changelog.py
set CHANGELOG_EXIT=!ERRORLEVEL!

rem 3d A4. This used to print [WARN] and swallow the exit code. The crawler
rem stamps every record with patch_date read from the file this step writes, so
rem a failed changelog fetch means a whole day of records stamped
rem `patch_date: null` - silently, and unrepairably once the day has passed.
rem A failed changelog fetch now fails the day, so the next logon retries it.
if not "!CHANGELOG_EXIT!"=="0" (
    echo.
    echo *********************************************************
    echo *  CHANGELOG FETCH FAILED - aborting before the crawl.  *
    echo *  Records would be stamped patch_date: null.           *
    echo *  Not stamped; the next logon will retry.              *
    echo *********************************************************
    exit /b !CHANGELOG_EXIT!
)

echo.
echo ==== [2/2] ascensionlogs crawl (max 25 new reports) ====
py tools\scrapers\crawl_ascensionlogs.py --max-reports 25
set CRAWL_EXIT=!ERRORLEVEL!

rem Exit 2 is the realm/season/phase refusal (season_config.RealmSeasonMismatch)
rem - it needs a human edit to season_config.py, not a retry.
if "!CRAWL_EXIT!"=="2" (
    echo.
    echo *********************************************************
    echo *  PHASE / REALM MISMATCH - season_config.py is stale.   *
    echo *  Nothing captured. Read the message above and edit it. *
    echo *********************************************************
)

if not exist "data\derived" mkdir "data\derived"

rem Stamp only on success. A failed run should be retried at the next logon,
rem not suppressed for the rest of the day.
if "!CRAWL_EXIT!"=="0" (
    echo !TODAY!> "%STAMP%"
    echo.
    echo *********************************
    echo *  DAILY CAPTURE: OK            *
    echo *********************************
) else (
    echo.
    echo *********************************************************
    echo *  DAILY CAPTURE FINISHED WITH ERRORS - read the summary *
    echo *********************************************************
)

exit /b !CRAWL_EXIT!
