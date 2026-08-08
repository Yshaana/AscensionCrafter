"""`3n` Block C (E2) — pair each KILL WINDOW to the stat block that describes the
character who produced it, and report what that pairing does and does not unlock.

🚨 **THIS IS THE T5 UNBLOCK, AND IT IS A PAIRING PROBLEM BEFORE IT IS A
REGRESSION PROBLEM.** `core/builds/inference.py :: infer_coefficient` returns
`refused:no_per_parse_stats` for every spell, because the crawl's armory
snapshot is gear-only and lags the parse. The Molten Core capture is the first
data that can lift that refusal for ONE character: six `AscensionCrafterExport`
stat blocks taken during a single raid, against combat logs with GUID-resolved
kill windows.

What this tool does, and deliberately does not do:

* it pairs each kill window to the **nearest stat block**, and reports the gap;
* it divides by **`logged_seconds`, never `wall_seconds`** — the Gehennas kill
  spans a client crash and the two differ by ~60 s (`3m` D). Dividing by wall
  understates DPS by ~16% on that window alone;
* it **refuses a pairing** whose stat blocks disagree across the window, because
  a stat that moved mid-parse is exactly the confound `2d` documented on Path of
  Duality — the character who produced the damage is then not the character the
  block describes;
* it **derives no coefficient here.** Which spells can carry one, and from what,
  is the prereg's business; this tool produces the *inputs* and says which are
  admissible. A coefficient fitted in the same breath as the pairing would be
  fitted to the parse it must later check.

🆕 `3o` Block B — GENERALISED, and its capture-gap constant retired.

It took a hardcoded folder, a hardcoded boss list, a hardcoded block count and a
hardcoded crash gap typed to whole seconds. It now takes any capture folder,
reads however many blocks the files hold, derives the gaps from the log files'
own millisecond stamps (`AUDIT_3N` F7 — see `core.logs.encounters
.derive_capture_gaps` for why that matters), and takes its window list from the
`/ace` addon's own `Target:` lines when the capture has them.

Run:  py tools/analysis/pair_parses_to_stats.py [--capture <folder>]
                                                [--bosses "A,B,C"]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config                                                   # noqa: E402
from core.builds.stat_block import parse_stat_block             # noqa: E402
from core.logs.encounters import (derive_capture_gaps,          # noqa: E402
                                  kill_window, scan_encounters)

config.ensure_utf8_stdout()

_HEADER_LINE = re.compile(r"^\s*===\s+.+\s+-\s+.+\s+-\s+.+\s+===\s*$")

CAPTURES = config.REPO / "data" / "source" / "captures"
DEFAULT_CAPTURE = CAPTURES / "2026-08-07_elric_mc_first_raid"

# The reference capture's encounter list. Kept as a NAMED DEFAULT for that one
# folder rather than a global: a dungeon capture has different bosses, and the
# `/ace` session blob names its own targets (see `_targets_from_blocks`).
MC_BOSSES = ["Lucifron", "Magmadar", "Gehennas", "Garr", "Baron Geddon",
             "Shazzrah", "Sulfuron Harbinger", "Golemagg the Incinerator"]

# 🛑 The pairing tolerance, STATED BEFORE THE PAIRING IS READ. A stat block
# describes the character at ONE instant; a parse spans minutes. A block is
# admissible for a window only if the stats did not move across it — which is
# checkable here, because the capture brackets the raid with six blocks rather
# than one. `2d`'s Path of Duality lesson is the reason this is a refusal and
# not a caveat: a stat that changes mid-parse means the character who produced
# the damage is not the character the block describes, and no amount of care
# downstream recovers it.
STAT_KEYS = ("attack_power", "strength", "agility", "intellect",
             "melee_crit_pct")


def _secs(hms, day=7, mon=8):
    h, m, s = (int(x) for x in hms.split(":"))
    return ((mon * 31 + day) * 86400.0 + h * 3600.0 + m * 60.0 + s)


def _load_lines(capture):
    """All combat-log lines, plus the PER-FILE line lists the gap derivation
    needs. Sorted by name first, then re-sorted by their own first timestamp
    inside `derive_capture_gaps` — a filename is a claim about ordering, a
    timestamp is evidence of it."""
    logs = sorted(capture.glob("*WoWCombatLog.txt"))
    per_file, lines = [], []
    for p in logs:
        with p.open(encoding="utf-8", errors="replace") as fh:
            fl = fh.readlines()
        per_file.append(fl)
        lines.extend(fl)
    return lines, per_file, [p.name for p in logs]


def _load_stat_blocks(capture):
    """Every AscensionCrafterExport block in the capture's non-log text files.

    ⚠ `Molten Core.txt` is TWO datasets in one file (stat blocks + 20
    inspects.nie.one links). The README says a naive parse trips on the URL
    lines, so blocks are split on their own header and the URLs never reach the
    parser.

    🆕 `3o` — every `.txt` that is not a combat log is scanned, not one named
    file, so a `/ace` session blob pasted into the folder is picked up with no
    code change. The block splitter is unchanged, which is exactly why the
    addon reuses one stat emitter.
    """
    parts = []
    for p in sorted(capture.glob("*.txt")):
        if "WoWCombatLog" in p.name:
            continue
        parts.append(p.read_text(encoding="utf-8", errors="replace"))
    text = "\n".join(parts)
    # ⚠ A block is delimited by its OWN `=== character - realm - season ===`
    # header, which is what `parse_stat_block` refuses without. An earlier draft
    # split on the literal "AscensionCrafterExport" — the addon's name, which
    # appears nowhere in the file — and parsed ZERO of six while reporting
    # "0 of 0", i.e. it could not tell "no blocks here" from "I looked for the
    # wrong thing". Hence the explicit expected-count check in main().
    lines_, blocks, cur = text.splitlines(keepends=True), [], None
    for ln in lines_:
        if _HEADER_LINE.match(ln):
            if cur:
                blocks.append("".join(cur))
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur:
        blocks.append("".join(cur))
    out = []
    for b in blocks:
        try:
            out.append(parse_stat_block(b))
        except Exception as e:                              # noqa: BLE001
            out.append({"error": f"{type(e).__name__}: {e}"})
    return out


def _targets_from_blocks(blocks):
    """Encounter names the `/ace` capture itself recorded, from its `Target:`
    lines. Free window-pairing hints: the addon writes the target's name and
    GUID at the instant combat began, so a dungeon capture names its own
    windows and no boss list has to be maintained per folder."""
    names = []
    for b in blocks:
        raw = (b.get("raw_fields") or {}).get("Target")
        if not raw or raw.strip() == "none":
            continue
        nm = raw.split(" / ")[0].strip()
        if nm and nm not in names:
            names.append(nm)
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", default=str(DEFAULT_CAPTURE),
                    help="capture folder (default: the 2026-08-07 MC raid)")
    ap.add_argument("--bosses", default=None,
                    help="comma-separated encounter names; default is the "
                         "capture's own /ace Target: lines, falling back to "
                         "the MC list for the reference capture")
    args = ap.parse_args()
    capture = Path(args.capture)
    if not capture.is_dir():
        alt = CAPTURES / args.capture
        if alt.is_dir():
            capture = alt
        else:
            print(f"🛑 no such capture folder: {args.capture}")
            return 1
    print(f"[capture] {capture.name}")

    lines, per_file, names = _load_lines(capture)
    print(f"[logs] {len(lines):,} lines from {len(names)} file(s): "
          f"{', '.join(names)}")

    # 🚨 `AUDIT_3N` F7 — the gaps are DERIVED from the files' own millisecond
    # stamps. The constant this replaces was typed to whole seconds and read
    # 60.0 where the bytes give 59.764, which shortened the Gehennas window and
    # inflated its DPS. `logged_seconds` is the denominator of every per-parse
    # coefficient, so a systematic truncation there is not a rounding question.
    gaps, spans = derive_capture_gaps(per_file)
    for i, (lo, hi) in enumerate(gaps):
        print(f"[gap]  a {hi - lo:.3f}s capture gap between file {i + 1} and "
              f"file {i + 2}, DERIVED from their own first/last event stamps "
              f"(not a hand-typed constant), subtracted from logged_seconds "
              f"wherever it overlaps a window")
    if not gaps:
        print("[gap]  no capture gaps — the log files are contiguous")

    blocks = _load_stat_blocks(capture)
    ok_blocks = [b for b in blocks if "error" not in b]
    print(f"\n[stats] {len(ok_blocks)} of {len(blocks)} stat blocks parsed")
    if not blocks:
        # 🛑 The guard that survives generalisation: "0 of 0" reads as "no data"
        # when it may mean "I looked for the wrong delimiter". That happened.
        print("    🛑 ZERO BLOCKS FOUND. Either this capture has no stat "
              "export, or the block delimiter has changed — those are "
              "different problems and this line refuses to conflate them.")
    for b in blocks:
        if "error" in b:
            print(f"    🛑 unparsed: {b['error']}")
    for b in ok_blocks:
        reason = (b.get("raw_fields") or {}).get("SnapshotReason")
        print(f"    ExportedAt {b.get('exported_at')}  "
              f"AP={b.get('attack_power')} "
              f"Str={b.get('strength')} Int={b.get('intellect')} "
              f"meleecrit={b.get('melee_crit_pct')}"
              + (f"  [{reason}]" if reason else ""))

    if args.bosses:
        bosses = [s.strip() for s in args.bosses.split(",") if s.strip()]
        src = "the --bosses argument"
    else:
        bosses = _targets_from_blocks(ok_blocks)
        src = "the capture's own /ace Target: lines"
        if not bosses and capture.name == DEFAULT_CAPTURE.name:
            bosses, src = MC_BOSSES, "the reference capture's known boss list"
    print(f"\n[windows] {len(bosses)} encounter name(s) from {src}")
    if not bosses:
        print("    🛑 NO ENCOUNTER NAMES. This capture carries no /ace "
              "`Target:` lines and none were passed — pass --bosses. Refusing "
              "to guess names out of the log.")
        return 1
    print("[windows] kill windows, GUID-resolved, wall vs LOGGED:")
    usable = 0
    for boss in bosses:
        enc = scan_encounters(lines, boss)
        if not enc:
            continue
        w = kill_window(lines, boss, gaps=gaps)
        if not w.get("ok"):
            print(f"\n  {boss:<26} 🛑 REFUSED — {w['reason'][:130]}")
            continue
        usable += 1
        print(f"\n  {boss:<26} wall {w['wall_seconds']:7.1f}s   "
              f"LOGGED {w['logged_seconds']:7.1f}s   "
              f"({w['attempts']} attempt(s), guid {w['guid']})")
        if w["wall_seconds"] - w["logged_seconds"] > 0.5:
            lost = w["wall_seconds"] - w["logged_seconds"]
            print(f"      ⚠ {lost:.1f}s of this window has NO LOG "
                  f"({100 * lost / w['wall_seconds']:.1f}%). Dividing damage by "
                  f"WALL here understates DPS by "
                  f"{100 * (1 - w['logged_seconds'] / w['wall_seconds']):.1f}%")
        for n in w.get("notes", []):
            print(f"      note: {n[:150]}")

    print(f"\n[summary] {usable} kill window(s) usable; "
          f"{len(ok_blocks)} stat block(s) parsed.")
    _report_pairing(lines, ok_blocks, gaps, bosses)
    return 0


def _block_secs(b):
    d = b.get("exported_at")
    return None if d is None else _secs(f"{d.hour:02d}:{d.minute:02d}:"
                                        f"{d.second:02d}", day=d.day, mon=d.month)


def _report_pairing(lines, blocks, gaps, bosses):
    """Pair each kill window with the stat blocks that BRACKET it, and rule on
    admissibility. The verdict is per window and is stated with its reason."""
    stamped = sorted(((_block_secs(b), b) for b in blocks if _block_secs(b)),
                     key=lambda t: t[0])
    print("\n[pairing] each kill window against the stat blocks bracketing it")
    print("          🛑 admissible only if the bracketing blocks AGREE — a stat "
          "that moved mid-parse means\n          the character who dealt the "
          "damage is not the character the block describes (2d).")
    verdicts = []
    for boss in bosses:
        w = kill_window(lines, boss, gaps=gaps)
        if not w.get("ok"):
            continue
        before = [t for t in stamped if t[0] <= w["start"]]
        after = [t for t in stamped if t[0] >= w["end"]]
        b0 = before[-1] if before else None
        b1 = after[0] if after else None
        if b0 is None and b1 is None:
            verdicts.append((boss, "REFUSED", "no stat block on either side"))
            continue
        if b0 is None:
            verdicts.append((boss, "REFUSED",
                             f"no stat block BEFORE this window (nearest after "
                             f"is +{b1[0] - w['end']:.0f}s) — the character's "
                             "state entering the parse is unknown"))
            continue
        if b1 is None:
            verdicts.append((boss, "REFUSED",
                             f"no stat block AFTER this window (nearest before "
                             f"is -{w['start'] - b0[0]:.0f}s) — nothing "
                             "confirms the stats held for the whole parse"))
            continue
        moved = [k for k in STAT_KEYS if b0[1].get(k) != b1[1].get(k)]
        if moved:
            deltas = ", ".join(f"{k} {b0[1].get(k)}->{b1[1].get(k)}"
                               for k in moved)
            verdicts.append((boss, "REFUSED",
                             f"the bracketing blocks DISAGREE ({deltas}); "
                             f"brackets -{w['start'] - b0[0]:.0f}s / "
                             f"+{b1[0] - w['end']:.0f}s"))
            continue
        verdicts.append((boss, "ADMISSIBLE",
                         f"AP={b0[1].get('attack_power')} held across the "
                         f"window (brackets -{w['start'] - b0[0]:.0f}s / "
                         f"+{b1[0] - w['end']:.0f}s); divide by "
                         f"{w['logged_seconds']:.1f}s LOGGED, not "
                         f"{w['wall_seconds']:.1f}s wall"))
    for boss, v, why in verdicts:
        mark = "✅" if v == "ADMISSIBLE" else "🛑"
        print(f"\n  {mark} {boss:<24} {v}")
        print(f"      {why}")
    n_ok = sum(1 for _, v, _ in verdicts if v == "ADMISSIBLE")
    print(f"\n[verdict] {n_ok} of {len(verdicts)} kill windows carry a stat "
          f"block pairing that survives the bracketing test.")
    if n_ok == 0:
        print("          E2 CANNOT derive a per-parse coefficient from this "
              "capture. That is a MEASUREMENT, not a shortfall of effort: the "
              "six blocks do not bracket any kill window with unchanged stats.")
        return
    # 🚨 IDENTIFIABILITY, and it is the finding this tool exists to reach.
    #
    # An admissible window supplies ONE (stat, damage) pair per ability. A
    # coefficient is a SLOPE: `damage = flat + coeff x stat`. One point cannot
    # separate the slope from the intercept — any coefficient whatsoever fits,
    # with the flat absorbing the remainder. Two points at MATERIALLY DIFFERENT
    # stat levels are the minimum, and they must be different in the stat being
    # fitted, not merely different parses.
    #
    # This is a DIFFERENT refusal from `refused:no_per_parse_stats`, and saying
    # so precisely is the whole value: the old blocker was "we have no stats at
    # the parse". That blocker is now LIFTED for this window. The new blocker is
    # "one admissible window is one point", which names exactly what the next
    # capture has to contain.
    if n_ok < 2:
        print(f"\n🛑 IDENTIFIABILITY REFUSAL — and it is NOT the old one.")
        print("   `refused:no_per_parse_stats` is LIFTED for the window(s) "
              "above: stats at the parse now exist, bracketed and verified\n"
              "   unchanged, with logged-vs-wall separated. That was E2's "
              "stated blocker and it is gone.")
        print(f"   What blocks a COEFFICIENT now is arithmetic: {n_ok} "
              "admissible window is ONE (stat, damage) point per ability, and\n"
              "   a coefficient is a SLOPE. `damage = flat + coeff x stat` is "
              "under-determined by one point — every coefficient fits, with\n"
              "   the flat absorbing the difference. Fitting one anyway would "
              "produce a confident number determined entirely by an\n"
              "   assumption about the flat, which is exactly what "
              "infer_coefficient refuses to do.")
        print("   WHAT WOULD LIFT IT: a second admissible window at a "
              "MATERIALLY DIFFERENT stat level for the same ability — not "
              "merely a\n   second parse. The capture already shows the stats "
              "moving (AP 488 -> 471 -> 331), so this is a capture-protocol "
              "problem,\n   not a data-availability one: take a stat block "
              "immediately BEFORE and AFTER each pull.")


if __name__ == "__main__":
    sys.exit(main() or 0)
