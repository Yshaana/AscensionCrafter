# Bug queue — things to report to Ascension

Game bugs and tooltip/log discrepancies worth reporting, staged here so they can be
submitted whenever there's time rather than lost in a session transcript.

**These are *game* bugs, not this repo's bugs.** Problems with our own code go in
`PROGRESS.md`'s plan-changes table or a session handoff, not here.

## Status meanings

| Status | Meaning |
|---|---|
| ✅ **ready** | Written up field-by-field, evidence holds, submit any time |
| 🔍 **needs verification** | Real discrepancy, but one check is missing before it's safe to report. The check is named on each row |
| 📤 submitted | Sent. Record the date and any response |
| 🔭 **watching** | Already reported by others (or by us) — **do not re-submit**. Tracked because it invalidates data or gates a recommendation. Watch the changelog for a fix and re-open what it unblocks |
| ❌ withdrawn | Turned out not to be a bug. **Keep the row** and say why — a withdrawn report is worth remembering |

## 🔭 Watch list — bugs whose FIX we must notice

A fix silently changes what our data means, so these are scanned against the
daily changelog capture (`data/source/changelog/daily/`). Keywords to scan for
are listed per row; on a hit, re-open the questions the bug file names.

| Bug | Changelog keywords | What a fix re-opens |
|---|---|---|
| [Path of Duality broken](bug_path-of-duality-broken.md) | `Duality`, `attack power`, `spell power`, `path` | The whole Duality path model, `elric_active_path_and_duality_ap_anomaly`, and the "ignore PoD logs" advisory |
| [Hammerdin trigger set](bug_hammerdin-trigger-set.md) (#200295) | `Hammerdin`, `Hour of Judgement`, `Holy Shock`, `Judgement`, `proc` | build doc §11 rotation priority — Judgement/Holy Shock would become engine-feeding again |

## Queue

| Status | Bug | Spell | File |
|---|---|---|---|
| 📤 **submitted 2026-08-04, diagnosis corrected same day** — [tracker #199929](https://ascension.gg/bugtracker/view/199929) | Tooltip damage range is inverted — displays "194 to 147" at level 60 where it should read 194 to 217. The maximum term scales at 1/level where the effect scales 2.4/level | `282987` Hammer from the Heavens | [bug_hammer-from-the-heavens-tooltip.md](bug_hammer-from-the-heavens-tooltip.md) |
| 🔍 needs verification | Damage school **changes across ranks of one card** — 0 → 32 (Shadow) → 1 (Physical). Found in session `1a`, recorded as an unresolved conflict; it is the only card in the pool that does this | Necrosis | — |
| 🔍 needs verification | Scaling **term type changes across ranks** — catalog rank scales from Spell Power (0.2), the level-60 rank scales from Attack Power (0.2). A stat swap between ranks of one ability is odd enough to be a data error | `281220` → `281224` Spirit Charge | — |
| 🔍 needs verification | **AP term disappears at higher rank** — catalog rank has SP 0.4 / AP 0.2, the level-60 rank has SP 1.3 and no AP term at all | `289100` → `289107` Sun Down | — |
| 🔍 needs verification | **db.ascension.gg and the client disagree by exactly 3×** on the per-level term — db renders 4.5/level, client DBC says 1.5. Open since `RECON_FINDINGS` | `276076` Fel Infused Weapon | — |
| 🔭 **watching** (community-reported, do NOT submit) | **Path of Duality is broken in ~6 ways** — AP bonus cycles on/off every ~10–15 s (832↔1128 for one player; 174↔307 for us), SP grant reduced to a flat ~19 (independently reported as 19), weapon-type passives dead, AP added after modifiers. **Owner decision: ignore PoD logs, don't recommend PoD, play PoI** | `129243` Path of Duality | [bug_path-of-duality-broken.md](bug_path-of-duality-broken.md) |
| ❌ withdrawn twice (same day) | **"Path switching leaves stats stale until relog"**, then **"~5–10 s settle delay"** — both superseded by the Duality AP **oscillation** above. Method lesson: a settle delay and an indefinite oscillation look identical through one before/after pair | — | [bug_path-switch-stale-stats.md](bug_path-switch-stale-stats.md) |
| 📤 **submitted 2026-08-05** — [tracker #200295](https://ascension.gg/bugtracker/view/200295) | **Hammerdin never procs from Holy Shock or Judgement** (1 proc / 129 casts vs ~26 expected at the tooltip's 20%; p < 10⁻⁹) while Dawnreaver and Hammer of Wrath proc normally and the −4 s reduction works per proc. Suspected cause: trigger-delivered damage is proc-blind | `282983` Hammerdin | [bug_hammerdin-trigger-set.md](bug_hammerdin-trigger-set.md) |

### What each 🔍 row still needs

- **Necrosis** — confirm the school really differs in play, not just in the data. A combat
  log showing the same card dealing two different schools at different ranks would settle
  it. Until then it could be intentional (a card that changes school as it ranks up is
  unusual but not impossible on this server).
- **Spirit Charge / Sun Down** — both come from comparing the *catalog* entry against the
  *level-60* entry, and the catalog stores Rank 1. Read the live in-game tooltip at the
  rank actually held before reporting; our rank resolution could be picking the wrong
  sibling, which would make this our bug and not theirs.
- **Fel Infused Weapon** — an in-game tooltip read at level 60 resolves it, and beats both
  sources. Note db was byte-faithful on Holy Supernova, so suspect a rank/variant mismatch
  (`276069` vs `276076`) or a stale snapshot before blaming either side.
- **Path-switch staleness** — whether *combat* uses the stale value or only the sheet/API
  does: ~20 dummy white swings right after a switch vs ~20 after relog, same gear. A ~+9%
  mean-swing shift = real gameplay bug; no shift = staleness in the character sheet only.

🛑 **Do not submit a 🔍 row.** Reporting a discrepancy that turns out to be our own
resolution error costs credibility on the reports that are real.

---

## The in-game form, and its constraints

`Create a Bug Report` window. Fields, in order:

| Field | Notes |
|---|---|
| **Category** \* | dropdown |
| **Priority** \* | dropdown |
| **Report Title** \* | ⚠ **50 characters maximum.** Put spell ids and figures in the Issue body instead |
| **Issue** \* | the main description |
| Is this a Gamebreaking Issue | Yes / No |
| Exact Location | "Manastorm, LFG, a raid, open world, HR etc." |
| What were you doing | |
| Expected Outcome | |
| Actual Outcome | |
| Steps to Reproduce | numbered `Step 1: / Step 2: / Step 3:` |
| Public Report | checkbox, on by default |

Buttons: `Talk to a GM` · `Create Issue`. The form also reminds you to verify your email
on ascension.gg.

**Submitted reports land at `https://ascension.gg/bugtracker/view/<id>`.**
⚠ **That page is auth-gated and cannot be read programmatically** — fetching it returns
the site's login form, even for a report submitted with `Public Report` checked. So a
report's status and any dev response have to be checked by the owner while logged in;
don't build anything that expects to poll the tracker. The Category and Priority dropdown
option lists are unknown for the same reason — fill them in here the next time the form
is open in-game.

## House style for these write-ups

- **Lead with what is undeniable**, then offer the diagnosis separately as help. A GM who
  rejects our analysis should still be left with a reproducible fact.
- **Keep our own parse/crawl data out of the report body.** It is strong evidence for us
  but invites questions about provenance, and the report rarely needs it. Put it in a
  "notes for us" section at the bottom of the file instead.
- **Label anything unverified as a prediction**, in the report and in our notes. Being
  wrong about a detail we flagged as a guess costs nothing; asserting it as measured does.
- **Say plainly what would change if they disagree** — e.g. "if the text is the intended
  damage, this is a damage bug, not a display bug." That is the follow-up worth tracking.
- **🔴 Separate the observation from the diagnosis, and label which is which.** Report
  #199929 had to be corrected the same day: the observation (the range is inverted) was
  right, but the offered cause was wrong and its suggested fix would have broken the part
  of the tooltip that was already correct. The report survived because the two were
  written as separate paragraphs — a dev could still act on the observation. **Had the
  diagnosis been woven into the description, the whole report would have been wrong.**
- **If a diagnosis turns out wrong, file the correction yourself** rather than leaving it.
  Volume of reports is worth less than a reporter whose reports can be trusted.
