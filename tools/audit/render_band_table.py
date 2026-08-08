#!/usr/bin/env python3
"""`3j` C3 — render the slice-accuracy band table FROM the gate manifest.

    py tools/audit/render_band_table.py            # print both blocks
    py tools/audit/render_band_table.py --check    # assert the doc matches

🆕 **`3m` pre-flight (`AUDIT_3L` F11) — this now renders TWO blocks, because
asserting the table alone left everything around it unowned.** `3l` regenerated
the band table (the arm fired and did its job) and the *prose derived from the
same manifest* went stale in the same commit: `:246` "At **26.3%**…", `:249` "a
**3.8×** rise", `:202` "roughly **ONE QUARTER**", and the `3i` A5 annotation's
producing-only pair. **Third time this file has staled inside its own
assertion's blind spot** — and each time the stale number sat within twenty
lines of a number the assertion was protecting.

The lesson is not "extend the regex". It is that a *derived* figure has the same
owner as the table it is derived from, so the DERIVED-FIGURES block below is
generated too, and the prose points at it instead of restating magnitudes. A
sentence that quotes no number cannot go stale.

**Why this exists.** `predictions/CALIBRATION_TOLERANCE.md`'s band table carries
its own standing warning — *"regenerate, do not retype, and check this table in
the same commit that moves the gate"* — and it has now gone stale **twice**:

* `3f`'s table survived `3g`, a session that regenerated the manifest five
  times. `3h` A2 regenerated it and wrote the warning above.
* `3i` moved the gate **twice** (E15, then admissibility) and did not touch the
  table. `AUDIT_3I` §9.3 measured the drift: doc `≥10% 23.4% (n=26)` against
  manifest `34.96% (n=27)`, doc `≥20% 20.5%` against manifest `26.31%`.

A warning that has been ignored twice by sessions that wrote it is not a
control. `CLAUDE.md`'s own rule is *a magnitude never appears in a markdown
file except as generated output* — and `3h` A4 already established the
follow-through: **generation only helps if something asserts the paste.** The
census line got that treatment; this table did not, and staled the same week.

So the table is generated here and `--check` is wired into `check_refusals.py`,
exactly like the `CLAUDE.md` census assertion.

Pure reporting: reads the committed manifest, opens no database, makes no
network request.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402

config.ensure_utf8_stdout()

MANIFEST = Path(__file__).resolve().parents[2] / "predictions" / "gate_manifest_3e.json"
DOC = Path(__file__).resolve().parents[2] / "predictions" / "CALIBRATION_TOLERANCE.md"

HEADER = "| coverage floor | n | median slice accuracy | readable? |"
_SEP = "|---:|---:|---:|:--|"

DERIVED_BEGIN = "<!-- GENERATED derived-figures (render_band_table.py) — DO NOT RETYPE -->"
DERIVED_END = "<!-- /GENERATED derived-figures -->"

# 1/n as an English ordinal word, for the "the sim reproduces roughly ONE X of
# the damage it has a key for" sentence. The sentence has been retyped and gone
# stale twice ("ONE FIFTH" at 20.5%, then "ONE QUARTER" at 26.3%), so the word
# is generated from the same number as everything else.
_ORDINALS = {2: "HALF", 3: "THIRD", 4: "QUARTER", 5: "FIFTH", 6: "SIXTH",
             7: "SEVENTH", 8: "EIGHTH", 9: "NINTH", 10: "TENTH"}


def _fraction_word(pct):
    """"roughly ONE THIRD" for 30.4, "ONE QUARTER" for 26.3, else a bare ratio."""
    if pct <= 0:
        return "an undefined fraction (slice accuracy is zero)"
    n = round(100.0 / pct)
    word = _ORDINALS.get(n)
    return f"roughly ONE {word}" if word else f"roughly 1/{n:g}"


def render_derived(manifest_path=MANIFEST):
    """The figures DERIVED from the manifest, as one asserted markdown block.

    Every number the surrounding prose used to state by hand lives here. The
    prose refers to this block by name and quotes nothing.
    """
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    r = m["result"]
    floor = r["slice_accuracy_coverage_floor_pct"]
    head = r["median_slice_accuracy_pct_at_coverage_ge_20"]
    prod = r["median_slice_accuracy_pct_producing_only_at_coverage_ge_20"]
    prod_n = r["producing_only_n"]
    head_n = r["slice_accuracy_by_coverage_band_pct"][f">={floor:g}"]["n"]
    paired = r.get("paired_medians_same_members_at_headline_floor") or {}

    cohort = m.get("cohort") or []
    # The cohort's best coverage — the most generous coverage assumption
    # available in reality, used to show that even it does not close the gap.
    # 🛑 Reported WITH its admissibility flag: at the time of writing the
    # highest-coverage member is NOT ADMISSIBLE (AUDIT_3L F8), and a figure that
    # hides that is the same lie the coverage-floor key was telling.
    best = max(cohort, key=lambda c: c.get("modelled_damage_pct") or 0.0) \
        if cohort else None

    lines = [
        DERIVED_BEGIN,
        "",
        "| derived figure | value | derived from |",
        "|---|---:|---|",
        (f"| headline slice accuracy (≥{floor:g}% coverage floor) "
         f"| **{head:.1f}% (n={head_n})** "
         f"| `median_slice_accuracy_pct_at_coverage_ge_{floor:g}` |"),
        (f"| …stated as a fraction of reality | **{_fraction_word(head)}** "
         f"| the same figure, rendered in words |"),
        (f"| multiple the slice must rise by at the 100% coverage CEILING "
         f"| **{100.0 / head:.1f}×** | `100 / headline` |"),
    ]
    if best is not None:
        cov = best.get("modelled_damage_pct") or 0.0
        flag = " — **NOT ADMISSIBLE**" if best.get("not_admissible") else ""
        lines += [
            (f"| best coverage anywhere in the cohort "
             f"| **{best.get('name')} {cov:.1f}%**{flag} "
             f"| `max(cohort[].modelled_damage_pct)` |"),
            # `delta = 0` needs slice × coverage = 1 with BOTH as fractions, so
            # the required slice in percent is 100 / (cov/100) = 10000/cov.
            # (Writing `100/cov` here gives 1.2% — an answer that reads as
            # trivially achievable when the real one exceeds 100% by
            # construction, i.e. exactly backwards.)
            (f"| …slice accuracy that coverage would require for `delta = 0` "
             f"| **{10000.0 / cov:.1f}%** | `100 / (best coverage / 100)` |"),
        ]
    lines += [
        (f"| producing-only slice median (≥{floor:g}%) "
         f"| **{prod:.1f}% (n={prod_n})** "
         f"| `median_slice_accuracy_pct_producing_only_at_coverage_ge_{floor:g}` |"),
    ]
    if paired:
        lines.append(
            f"| …paired over the SAME members (no selection bias) "
            f"| **{paired.get('headline_pct')}% headline / "
            f"{paired.get('producing_only_pct')}% producing-only "
            f"(n={paired.get('n')})** "
            f"| `paired_medians_same_members_at_headline_floor` |")
    lines += [
        "",
        (f"*(from `{MANIFEST.name}`, generated {m['generated_at']}, "
         f"git `{m['git_sha'][:7]}`.)*"),
        "",
        DERIVED_END,
    ]
    return "\n".join(lines), m


def extract_derived_from_doc(doc_path=DOC):
    """The derived-figures block as it currently stands in the document."""
    text = doc_path.read_text(encoding="utf-8")
    i = text.find(DERIVED_BEGIN)
    if i < 0:
        return None
    j = text.find(DERIVED_END, i)
    if j < 0:
        return None
    return text[i:j + len(DERIVED_END)].strip()


def render(manifest_path=MANIFEST):
    """The band table as markdown, plus the manifest's own provenance."""
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    bands = m["result"]["slice_accuracy_by_coverage_band_pct"]
    floor = m["result"]["slice_accuracy_coverage_floor_pct"]
    lines = [HEADER, _SEP]
    for key in sorted(bands, key=lambda k: float(k.lstrip(">="))):
        b = bands[key]
        pct = float(key.lstrip(">="))
        emph = "**" if pct == floor else ""
        readable = ("yes" if b["readable"]
                    else "**no** — below the floor")
        lines.append(f"| ≥{pct:g}% | {emph}{b['n']}{emph} | "
                     f"{emph}{b['median_pct']:.1f}%{emph} | {readable} |")
    return "\n".join(lines), m


def extract_from_doc(doc_path=DOC):
    """The table as it currently stands in the document, normalised."""
    text = doc_path.read_text(encoding="utf-8")
    i = text.find(HEADER)
    if i < 0:
        return None
    out = []
    for ln in text[i:].splitlines():
        if not ln.startswith("|"):
            break
        out.append(ln.rstrip())
    return "\n".join(out)


def main():
    table, m = render()
    derived, _ = render_derived()
    if "--check" not in sys.argv:
        print(table)
        print(f"\n(from {MANIFEST.name}, generated {m['generated_at']}, "
              f"git {m['git_sha'][:7]})\n")
        print(derived)
        return 0

    rc = 0
    doc = extract_from_doc()
    if doc is None:
        print(f"🛑 [C3] FAIL — the band table header was not found in "
              f"{DOC.name}; cannot verify")
        rc = 1
    elif _norm(doc) != _norm(table):
        print(f"🛑 [C3] FAIL — {DOC.name}'s band table disagrees with "
              f"{MANIFEST.name}.\n--- document ---\n{doc}\n"
              f"--- manifest ---\n{table}")
        rc = 1
    else:
        print(f"PASS  [C3] {DOC.name}'s band table EQUALS the one generated "
              f"from {MANIFEST.name}")

    # 🆕 3m (AUDIT_3L F11) — the block the PROSE reads from is asserted too.
    # Asserting the table alone is what let "26.3%" / "3.8×" / "ONE QUARTER"
    # survive a session that regenerated the table correctly.
    doc_d = extract_derived_from_doc()
    if doc_d is None:
        print(f"🛑 [3m-A0] FAIL — the derived-figures block was not found in "
              f"{DOC.name}; the prose's numbers have no owner again")
        rc = 1
    elif _norm(doc_d) != _norm(derived):
        print(f"🛑 [3m-A0] FAIL — {DOC.name}'s DERIVED-FIGURES block disagrees "
              f"with {MANIFEST.name}.\n--- document ---\n{doc_d}\n"
              f"--- manifest ---\n{derived}")
        rc = 1
    else:
        print(f"PASS  [3m-A0] {DOC.name}'s derived-figures block EQUALS the "
              f"one generated from {MANIFEST.name} — the prose around the "
              f"table has the same owner the table does")
    return rc


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


if __name__ == "__main__":
    sys.exit(main())
