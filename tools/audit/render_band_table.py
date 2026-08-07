#!/usr/bin/env python3
"""`3j` C3 — render the slice-accuracy band table FROM the gate manifest.

    py tools/audit/render_band_table.py            # print it
    py tools/audit/render_band_table.py --check    # assert the doc matches

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
    if "--check" not in sys.argv:
        print(table)
        print(f"\n(from {MANIFEST.name}, generated {m['generated_at']}, "
              f"git {m['git_sha'][:7]})")
        return 0
    doc = extract_from_doc()
    if doc is None:
        print(f"🛑 [C3] FAIL — the band table header was not found in "
              f"{DOC.name}; cannot verify")
        return 1
    if _norm(doc) != _norm(table):
        print(f"🛑 [C3] FAIL — {DOC.name}'s band table disagrees with "
              f"{MANIFEST.name}.\n--- document ---\n{doc}\n"
              f"--- manifest ---\n{table}")
        return 1
    print(f"PASS  [C3] {DOC.name}'s band table EQUALS the one generated from "
          f"{MANIFEST.name}")
    return 0


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


if __name__ == "__main__":
    sys.exit(main())
