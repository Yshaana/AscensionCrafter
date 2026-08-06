@echo off
rem =====================================================================
rem  AscensionCrafter PHASE 1 BASELINE - one-shot scheduled entry point.
rem
rem  Why this exists as a scheduled task at all: leaderboard standings and
rem  armory snapshots are the ONLY genuinely unrecoverable data at a phase
rem  flip. Reports persist, so the report backfill has no deadline - but
rem  "what the Phase 1 meta looked like" is gone the moment Phase 2 lands
rem  on 2026-08-08. A capture already exists from 2026-08-04; this run
rem  tightens the "before" edge to the last practical day.
rem
rem  Re-running OVERWRITES data/source/crawl/baseline_phase1/ in place.
rem  That is intended - it is a point-in-time artifact and each record is
rem  dated internally, so the newer snapshot simply replaces the older one.
rem
rem  No `pause`: Task Scheduler has nobody to press a key, and a pause
rem  would hang the task until the time limit killed it.
rem
rem  Registered by register_phase1_baseline.ps1. See SCHEDULING.md.
rem =====================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0..\.."

set STAMP=data\derived\last_baseline_capture.txt

rem Guard against a catch-up run firing twice (StartWhenAvailable can fire
rem late, and the task is deliberately left registered afterwards so the
rem run is auditable rather than vanishing on success).
for /f %%d in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd\")"') do set TODAY=%%d
if exist "%STAMP%" (
    set /p LASTRUN=<"%STAMP%"
    if "!LASTRUN!"=="!TODAY!" (
        echo [skip] Baseline already captured today ^(!TODAY!^). Nothing to do.
        exit /b 0
    )
)

echo.
echo ==== Phase 1 baseline snapshot (top 50 characters + leaderboards) ====
py tools\scrapers\baseline_phase1.py --top 50
set EXITCODE=!ERRORLEVEL!

rem 3f F0 - exit 2 is a REFUSAL, not a failure, and the difference matters:
rem "will retry" is wrong advice for a phase flip. The refusal banner on stderr
rem says the capture is no longer possible; re-running would only produce a
rem POST-flip snapshot in a folder named baseline_phase1.
if "!EXITCODE!"=="2" (
    echo.
    echo *********************************************************
    echo *  PHASE ASSERTION REFUSED THE BASELINE - DO NOT RETRY   *
    echo *  Read the banner above. If the flip has happened, the  *
    echo *  pre-flip baseline is gone and the newest usable one   *
    echo *  is whatever is already committed. Reports persist.    *
    echo *********************************************************
    exit /b 2
)

if not "!EXITCODE!"=="0" (
    echo.
    echo *********************************************************
    echo *  BASELINE CAPTURE FAILED - not stamped, will retry     *
    echo *********************************************************
    exit /b !EXITCODE!
)

if not exist "data\derived" mkdir "data\derived"
echo !TODAY!> "%STAMP%"

echo.
echo ==== Committing the baseline (tier 1, irreplaceable) ====
rem Scope the commit to the baseline folder ONLY. This task runs unattended
rem and must never sweep up unrelated working-tree changes.
git add data/source/crawl/baseline_phase1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Phase 1 baseline re-capture before the 2026-08-08 phase flip" -m "Scheduled one-shot run. Leaderboard standings and armory snapshots are the only data a phase flip destroys; reports persist. Overwrites the 2026-08-04 capture in place - point-in-time artifact, records dated internally." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
    git push
    if errorlevel 1 echo [WARN] push failed - the commit is local, push it by hand.
) else (
    echo [note] Baseline output is byte-identical to the committed copy - nothing to commit.
)

echo.
echo *********************************
echo *  PHASE 1 BASELINE: OK         *
echo *********************************
exit /b 0
