<#
.SYNOPSIS
    Register the ONE-SHOT Phase 1 baseline re-capture, to run before the
    2026-08-08 phase flip. Scripted rather than hand-clicked so it is
    reproducible and reviewable in git.

.DESCRIPTION
    Owner decision 2026-08-05: re-run the baseline on the 7th to tighten the
    "before" edge. A capture already exists from 2026-08-04; this replaces it.

    Why a dated one-time trigger rather than the at-logon pattern the daily
    crawl uses: this is not a recurring habit, it is a deadline. The logon
    trigger exists because "when I turn on the computer" is the owner's daily
    rhythm; a phase flip happens at a fixed date whether or not he logs on.

    Settings, and the reasoning that differs from the daily task:
      * One-time trigger, 2026-08-07 20:00 local - late enough to be the last
        practical "before" reading, early enough to leave the whole evening
        (and, via StartWhenAvailable, the 8th's boot) as slack.
      * StartWhenAvailable ON        - THE important one. If the PC is off at
                                       20:00 the task fires at the next boot
                                       instead of being silently skipped.
      * network condition ON         - no point firing offline
      * ExecutionTimeLimit 2 hours   - the 2026-08-04 run took minutes; 2h
                                       catches a hang without killing a slow run
      * WakeToRun OFF                - do not wake the machine for this
      * RunLevel Limited             - the manual run never needed elevation
      * Logon type Interactive       - no stored password, console visible

    The task is deliberately NOT self-deleting. A task that vanishes on success
    leaves no evidence it ran; the batch carries its own once-per-day guard, and
    `-Unregister` removes it once the phase has flipped.

.PARAMETER Unregister
    Remove the task instead of creating it. Run this after 2026-08-08.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\scheduling\register_phase1_baseline.ps1
    powershell -ExecutionPolicy Bypass -File tools\scheduling\register_phase1_baseline.ps1 -Unregister
#>
[CmdletBinding()]
param(
    [string]$TaskName = 'AscensionCrafter Phase1 Baseline',
    [datetime]$RunAt = '2026-08-07 20:00:00',
    [switch]$Unregister
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$batch = Join-Path $repo 'tools\scheduling\run_baseline_scheduled.bat'

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
if ($RunAt -lt (Get-Date)) {
    Write-Warning ("$RunAt is in the PAST. Registering anyway - StartWhenAvailable " +
                   "means it will fire almost immediately. Pass -RunAt to change it.")
}

$action = New-ScheduledTaskAction -Execute 'cmd.exe' `
    -Argument "/c `"$batch`"" -WorkingDirectory $repo

$trigger = New-ScheduledTaskTrigger -Once -At $RunAt

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -DontStopOnIdleEnd `
    -MultipleInstances IgnoreNew
$settings.DisallowStartIfOnBatteries = $false
$settings.StopIfGoingOnBatteries = $false
$settings.WakeToRun = $false

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "Replaced the existing '$TaskName' task."
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal `
    -Description ("ONE-SHOT: re-capture the Phase 1 baseline (leaderboards + top " +
                  "50 armory snapshots) before the 2026-08-08 phase flip. Those " +
                  "are the only data a phase flip destroys - reports persist. " +
                  "Overwrites data/source/crawl/baseline_phase1/ in place, then " +
                  "commits and pushes that folder only. Remove after the flip " +
                  "with -Unregister. See SCHEDULING.md.") | Out-Null

Write-Output "Registered '$TaskName'."
Write-Output ""
Get-ScheduledTask -TaskName $TaskName |
    Select-Object TaskName, State,
        @{n = 'RunAt'; e = { $_.Triggers[0].StartBoundary } },
        @{n = 'StartWhenAvailable'; e = { $_.Settings.StartWhenAvailable } },
        @{n = 'NetworkRequired'; e = { $_.Settings.RunOnlyIfNetworkAvailable } },
        @{n = 'TimeLimit'; e = { $_.Settings.ExecutionTimeLimit } },
        @{n = 'WakeToRun'; e = { $_.Settings.WakeToRun } },
        @{n = 'RunLevel'; e = { $_.Principal.RunLevel } },
        @{n = 'LogonType'; e = { $_.Principal.LogonType } } |
    Format-List

Write-Output "Test it now (it will really capture + commit) with:"
Write-Output "  schtasks /run /tn `"$TaskName`""
Write-Output "Remove it after the flip with:"
Write-Output "  powershell -ExecutionPolicy Bypass -File tools\scheduling\register_phase1_baseline.ps1 -Unregister"
