# Scheduled data capture

The daily crawl runs automatically. The historical backfill deliberately does not.

---

## What is scheduled

| | |
|---|---|
| **Task name** | `AscensionCrafter Daily Crawl` |
| **Runs** | `tools/scheduling/run_crawler_scheduled.bat` |
| **Trigger** | **At logon**, 5 minutes after you log in |
| **Frequency** | At most **once per day**, even if you log on several times |
| **Time limit** | 2 hours, then Windows stops it |
| **Network** | Only starts if a network connection is available |
| **Wake the PC** | No |
| **Privileges** | Normal (not elevated) |
| **Logon** | Runs only while you are logged on — no stored password |

It does the same two things a manual `run_crawler.bat` does: snapshot the changelog,
then crawl `darkmoon.ascensionlogs.gg` capped at 25 new reports, then commit and push
`data/source`.

**Why at logon rather than a fixed time.** You said "when I turn on the computer",
and that is what a logon trigger means. It also makes the whole missed-run question
disappear: a PC that was off simply has not logged on yet, so there is no missed run
to catch up — the next logon *is* the run. Nothing needs to be scheduled for 09:00
and then rescued.

**Why the once-per-day guard is in the batch file, not the trigger.** Logging on
twice in a day is normal and must not mean crawling twice. `run_crawler_scheduled.bat`
writes `data/derived/last_scheduled_crawl.txt` after a **successful** run and exits
early if that file already says today. Failures are not stamped, so a broken run
retries at the next logon instead of being suppressed for the rest of the day.

Running twice in one day is safe anyway — `scan_log.json` skips reports already
captured, and armory records are content-hashed and only rewritten when a build
actually changed. The guard is there to avoid pointless load on someone else's public
API, not to prevent corruption.

---

## Doing things to it

Re-register after changing any setting (it replaces the existing task):

```bash
powershell -ExecutionPolicy Bypass -File tools\scheduling\register_daily_crawler.ps1
```

Run it right now without waiting for a logon:

```bash
schtasks /run /tn "AscensionCrafter Daily Crawl"
```

Check when it last ran and whether it worked (`LastTaskResult` `0` is success,
`267009` means it is running right now):

```bash
powershell -NoProfile -Command "Get-ScheduledTaskInfo -TaskName 'AscensionCrafter Daily Crawl'"
```

Turn it off for a while, and back on:

```bash
powershell -NoProfile -Command "Disable-ScheduledTask -TaskName 'AscensionCrafter Daily Crawl'"
```

```bash
powershell -NoProfile -Command "Enable-ScheduledTask -TaskName 'AscensionCrafter Daily Crawl'"
```

Remove it entirely:

```bash
powershell -ExecutionPolicy Bypass -File tools\scheduling\register_daily_crawler.ps1 -Unregister
```

**Change the delay after logon** (default 5 minutes) with
`-DelayMinutes 15`. **Change the task name** with `-TaskName`. If you ever want a
fixed clock time instead of at-logon, that is a one-line change in
`register_daily_crawler.ps1` — swap `New-ScheduledTaskTrigger -AtLogOn` for
`-Daily -At 9am`; `StartWhenAvailable` is already on, so a missed run would still
fire when the PC came back.

**Force a re-run today** after it has already run — delete the stamp:

```bash
del data\derived\last_scheduled_crawl.txt
```

Or just double-click `run_crawler.bat`, which ignores the guard entirely. A manual
run is an explicit act and should always run.

---

## 🛑 The catchup backfill is NOT scheduled, on purpose

`catchup_crawler.bat` is uncapped: it walks report IDs upward until it hits 20
consecutive missing ones, and grind reports take ~10 minutes each, so a full pass can
run for hours.

**Do not automate it.** An unbounded unattended job hammering a third-party public API
is exactly what the crawler's sequential, rate-limited design exists to avoid, and the
likeliest outcome of getting it wrong is the IP or account being blocked — which would
cost far more than the backfill is worth. It stays a deliberate manual action you start
before bed.

There is no deadline on it either. Reports persist on ascensionlogs after a phase
flips, so the historical parse data is not going anywhere.

---

## Two files, and which is which

| File | Used by | Has `pause` | Honours the once-per-day guard |
|---|---|---|---|
| `run_crawler.bat` | you, double-clicking | yes | **no** — always runs |
| `tools/scheduling/run_crawler_scheduled.bat` | Task Scheduler | no | yes |

The scheduled one has no `pause` because there is nobody to press a key — a pause
would hang the task until the 2-hour limit killed it.

---

## One-shot: Phase 1 baseline before the 2026-08-08 flip

**Task:** `AscensionCrafter Phase1 Baseline` · **fires** 2026-08-07 20:00 local ·
**registered by** `tools/scheduling/register_phase1_baseline.ps1` ·
**runs** `tools/scheduling/run_baseline_scheduled.bat`

Owner decision 2026-08-05. A capture already exists from 2026-08-04; this
tightens the "before" edge to the last practical day.

**Why it is worth a scheduled task at all.** Leaderboard standings and armory
snapshots are the *only* data a phase flip destroys — **reports persist**, so the
report backfill has no deadline. "What the Phase 1 meta looked like" is gone the
moment Phase 2 lands.

**Why a dated one-time trigger, not the at-logon pattern.** The daily crawl uses
at-logon because "when I turn on the computer" is the owner's rhythm. This is not
a habit, it is a deadline — a phase flips on a fixed date whether or not anyone
logs on. **`StartWhenAvailable` is the load-bearing setting**: if the PC is off at
20:00 the task fires at the next boot instead of being silently skipped.

**What it does:** re-runs `baseline_phase1.py --top 50`, **overwriting**
`data/source/crawl/baseline_phase1/` in place (intended — it is a point-in-time
artifact and every record is dated internally), then commits **that folder only**
and pushes. Scoping the commit matters: the task runs unattended and must never
sweep up unrelated working-tree changes. It carries its own once-per-day guard
(`data/derived/last_baseline_capture.txt`) so a late catch-up run cannot fire twice,
and it stamps **only on success** so a failure retries rather than being suppressed.

**Afterwards — remove it.** The task deliberately does not self-delete (a task
that vanishes on success leaves no evidence it ran):

```bash
powershell -ExecutionPolicy Bypass -File tools/scheduling/register_phase1_baseline.ps1 -Unregister
```
