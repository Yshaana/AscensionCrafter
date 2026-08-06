@echo off
rem =====================================================================
rem  AscensionCrafter DBC EXTRACT - double-click to run (session 3b)
rem
rem  Reads the game client's own Spell.dbc and rebuilds the database from
rem  it. Run this after a client patch, or when Claude asks for it.
rem
rem  WHAT IT NEEDS
rem    * The Ascension client installed
rem    * A built StormLib.dll (set STORMLIB_DLL if it is not in the
rem      default place - this script checks and tells you)
rem    * THE GAME CLOSED. The client locks the files this reads.
rem
rem  IT IS SAFE TO RE-RUN. Nothing is deleted that cannot be rebuilt, and
rem  running it twice produces the same result as running it once.
rem
rem  A full log is written to dbc_extract_log.txt next to this file. If
rem  anything goes wrong, send Claude that file.
rem =====================================================================
setlocal
cd /d "%~dp0"
set LOG=%~dp0dbc_extract_log.txt
echo AscensionCrafter DBC extract - %DATE% %TIME% > "%LOG%"

echo.
echo ================================================================
echo   AscensionCrafter - DBC extract
echo ================================================================
echo.
echo   Before continuing, please make sure the GAME IS CLOSED.
echo   (The client locks the files this needs to read.)
echo.
pause

rem ---------------------------------------------------------------- 0/4
echo.
echo ==== [0/4] Checking the game is not running ====
rem Absolute paths on purpose. If Git for Windows' usr\bin is ahead of
rem System32 on PATH, its Unix `find` and `tasklist` shadow the Windows
rem ones - the check then errors out and reports "game is closed" without
rem having checked anything, i.e. it FAILS OPEN. Caught in a dry run.
set "TASKLIST=%SystemRoot%\System32\tasklist.exe"
set "FIND=%SystemRoot%\System32\find.exe"
if not exist "%TASKLIST%" goto :nocheck
if not exist "%FIND%" goto :nocheck

"%TASKLIST%" /FI "IMAGENAME eq Ascension.exe" 2>nul | "%FIND%" /I "Ascension.exe" >nul
if not errorlevel 1 (
    echo.
    echo   [STOP] Ascension.exe is still running.
    echo   Close the game completely, then run this again.
    echo.
    echo Ascension.exe was running - aborted >> "%LOG%"
    pause
    exit /b 1
)
"%TASKLIST%" /FI "IMAGENAME eq Wow.exe" 2>nul | "%FIND%" /I "Wow.exe" >nul
if not errorlevel 1 (
    echo.
    echo   [STOP] Wow.exe is still running.
    echo   Close the game completely, then run this again.
    echo.
    echo Wow.exe was running - aborted >> "%LOG%"
    pause
    exit /b 1
)
echo   OK - game is closed.
goto :checked

:nocheck
rem Never pretend the check passed when it could not run.
echo   [WARN] Could not check whether the game is running.
echo   Please confirm yourself that Ascension is fully closed.
echo could not run the game-running check >> "%LOG%"
pause

:checked

rem ---------------------------------------------------------------- 1/4
echo.
echo ==== [1/4] Getting the latest code ====
git pull >> "%LOG%" 2>&1
if errorlevel 1 (
    echo.
    echo   [STOP] "git pull" failed. Nothing has been changed.
    echo   Send Claude the file: dbc_extract_log.txt
    echo.
    pause
    exit /b 1
)
echo   OK - code is up to date.

rem ---------------------------------------------------------------- 2/4
echo.
echo ==== [2/4] Checking the spell-id list is present ====
if not exist "data\source\dbc\extract_scope_observed_ids.json" (
    echo.
    echo   [STOP] data\source\dbc\extract_scope_observed_ids.json is missing.
    echo   Without it the extract will NOT pick up the spells we need,
    echo   so there is no point running it. Tell Claude.
    echo.
    echo scope file missing - aborted >> "%LOG%"
    pause
    exit /b 1
)
echo   OK - spell-id list found.

rem ---------------------------------------------------------------- 3/4
echo.
echo ==== [3/4] Reading the client and rebuilding (a few minutes) ====
echo   Leave this window open. Progress appears below.
echo.
rem Shows progress live AND writes it to the log, so a failure is
rem diagnosable without you having to copy anything out of the window.
rem (Tee-Object writes UTF-16 in Windows PowerShell 5.1, which garbles the
rem log, so the output is collected and written out as UTF-8 instead.)
powershell -NoProfile -ExecutionPolicy Bypass -Command "py cli\rebuild.py --with-dbc 2>&1 | Tee-Object -Variable out; $out | Out-File -FilePath '%LOG%' -Append -Encoding utf8; exit $LASTEXITCODE"
set REBUILD_EXIT=%ERRORLEVEL%

rem ---------------------------------------------------------------- 4/4
echo.
echo ==== [4/4] Result ====
if not "%REBUILD_EXIT%"=="0" (
    echo.
    echo   *********************************************************
    echo   *  IT DID NOT FINISH - and nothing is broken.           *
    echo   *********************************************************
    echo.
    echo   Most likely one of these:
    echo     - StormLib.dll not found  ^(set STORMLIB_DLL^)
    echo     - the client is not at the expected folder
    echo     - the game was still running
    echo.
    echo   Send Claude the file: dbc_extract_log.txt
    echo.
    pause
    exit /b 1
)

echo.
echo   *********************************************************
echo   *  DONE - the extract worked.                           *
echo   *********************************************************
echo.
echo   Two files were updated:
echo     data\source\dbc\dbc-extract.json
echo     data\source\dbc\dbc-ascension-extract.json
echo.
echo   These are meant to change - that is the point of the run.
echo.
echo   NOTHING HAS BEEN UPLOADED. Claude will check the results
echo   first and commit them. Just tell Claude it is done.
echo.
pause
endlocal
