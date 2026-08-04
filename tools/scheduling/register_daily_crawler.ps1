<#
.SYNOPSIS
    Register (or re-register) the daily AscensionCrafter crawl as a Windows
    scheduled task. Scripted rather than hand-clicked so it is reproducible.

.DESCRIPTION
    Trigger: AT LOGON, not a fixed clock time. The owner's stated pattern is
    "when I turn on the computer", and a logon trigger matches that exactly —
    with the bonus that "run as soon as possible after a missed start" becomes
    moot, because a PC that was off simply has not logged on yet.

    Logging on more than once a day is normal, so the once-per-day guard lives
    in run_crawler_scheduled.bat rather than in the trigger.

    Settings applied, per TASK_automate_daily_crawler.md:
      * 5-minute delay after logon      - don't fight startup for CPU/network
      * StartWhenAvailable               - catch-up behaviour
      * network condition ON             - no point firing offline
      * ExecutionTimeLimit 2 hours       - the daily run is bounded to ~30-60 min,
                                           so 2h catches a hang without killing a
                                           legitimately long run
      * WakeToRun OFF                    - the PC is already on; don't add wake
      * RunLevel Limited (not elevated)  - manual runs never needed elevation
      * Logon type Interactive           - runs only when logged on, so no stored
                                           password and the console is visible

.PARAMETER Unregister
    Remove the task instead of creating it.

.EXAMPLE
    py -3 -c ""   # (nothing to do with python; see below)
    powershell -ExecutionPolicy Bypass -File tools\scheduling\register_daily_crawler.ps1
    powershell -ExecutionPolicy Bypass -File tools\scheduling\register_daily_crawler.ps1 -Unregister
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'AscensionCrafter Daily Crawl',
    [int]$DelayMinutes = 5,
    [switch]$Unregister
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$batch = Join-Path $repo 'tools\scheduling\run_crawler_scheduled.bat'

if ($Unregister) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Output "Removed scheduled task '$TaskName'."
    } else {
        Write-Output "No scheduled task named '$TaskName' - nothing to remove."
    }
    return
}

if (-not (Test-Path $batch)) {
    throw "Cannot find $batch - is this script still inside the repo?"
}

$action = New-ScheduledTaskAction -Execute 'cmd.exe' `
    -Argument "/c `"$batch`"" -WorkingDirectory $repo

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
# PS 5.1's -AtLogOn trigger has no -RandomDelay/-Delay parameter; the delay is a
# property on the CIM object and has to be set as an ISO 8601 duration.
$trigger.Delay = "PT${DelayMinutes}M"

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -DontStopOnIdleEnd `
    -MultipleInstances IgnoreNew
$settings.DisallowStartIfOnBatteries = $false
$settings.StopIfGoingOnBatteries = $false
$settings.WakeToRun = $false

# Interactive = "run only when the user is logged on". No password is stored and
# nothing has to be typed at registration time.
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "Replaced the existing '$TaskName' task."
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal `
    -Description ("Daily AscensionCrafter capture: changelog snapshot + " +
                  "ascensionlogs crawl (max 25 new reports), then auto-commit. " +
                  "Runs at logon, at most once per day. The catchup backfill is " +
                  "deliberately NOT scheduled - see SCHEDULING.md.") | Out-Null

Write-Output "Registered '$TaskName'."
Write-Output ""
Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State,
        @{n = 'Trigger'; e = { $_.Triggers[0].CimClass.CimClassName } },
        @{n = 'Delay'; e = { $_.Triggers[0].Delay } },
        @{n = 'StartWhenAvailable'; e = { $_.Settings.StartWhenAvailable } },
        @{n = 'NetworkRequired'; e = { $_.Settings.RunOnlyIfNetworkAvailable } },
        @{n = 'TimeLimit'; e = { $_.Settings.ExecutionTimeLimit } },
        @{n = 'WakeToRun'; e = { $_.Settings.WakeToRun } },
        @{n = 'RunLevel'; e = { $_.Principal.RunLevel } },
        @{n = 'LogonType'; e = { $_.Principal.LogonType } } |
    Format-List

Write-Output "Run it once now with:  schtasks /run /tn `"$TaskName`""
