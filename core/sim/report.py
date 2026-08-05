"""Phase 2 T11 — rendering. A PURE FORMATTER, with no logic in the renderer.

Three outputs from the same structured dict: a plain dict (the source of truth),
a terminal table, and a self-contained HTML page. The HTML path is what the
eventual web UI grows from, which is exactly why nothing here may compute — a
number that appears only in a rendering is a number no test can reach.

⚠ **Warnings are rendered, never summarised away.** Every tier in this stack
carries `warnings` naming its unvalidated assumptions, and a report that hides
them behind a count turns an honest model into a confident one. The HTML puts
them in a `<details>` so they are collapsed but present, and the terminal view
prints them in full unless explicitly limited.
"""
import html
import json


# --- terminal ------------------------------------------------------------------

def render_sim_result(result, *, max_warnings=None):
    """A SimResult (or its dict form) as a terminal table."""
    d = result if isinstance(result, dict) else _sim_result_dict(result)
    lines = [
        f"=== {d['tier'].upper()}  [{d.get('apl_name') or 'no APL'}]",
        f"    {d['primary_metric']}: {d['primary_value']:,.0f}   "
        f"(content: {d.get('content_name')})",
        "",
        f"    {'ability':32}{'casts':>7}{'damage':>12}{'share':>8}  notes",
    ]
    total = sum(r.get("damage", 0.0) for r in d["per_ability"].values()) or 1.0
    for _sid, row in sorted(d["per_ability"].items(),
                            key=lambda kv: -kv[1].get("damage", 0.0)):
        note = "ATTRIBUTED" if row.get("attributed") else ""
        lines.append(
            f"    {str(row.get('name'))[:31]:32}{row.get('casts', 0):>7.1f}"
            f"{row.get('damage', 0.0):>12,.0f}"
            f"{100 * row.get('damage', 0.0) / total:>7.1f}%  {note}")
    warnings = d.get("warnings") or []
    if warnings:
        shown = warnings if max_warnings is None else warnings[:max_warnings]
        lines += ["", f"--- warnings ({len(warnings)})"]
        lines += [f"  * {w}" for w in shown]
        if len(shown) < len(warnings):
            lines.append(f"  ... and {len(warnings) - len(shown)} more")
    return "\n".join(lines)


def render_diff(diff):
    """A `diff_builds` result as a terminal table."""
    lines = [
        "=== BUILD DIFF",
        f"    A {diff['dps_a']:,.0f}   B {diff['dps_b']:,.0f}   "
        f"delta {diff['delta']:+,.0f}"
        + (f" ({diff['delta_pct']:+.1f}%)" if diff.get("delta_pct") else ""),
        "",
        f"    VERDICT: {diff['verdict'].upper()}"
        + (f"  -> {diff['winner'].upper()} wins" if diff.get("winner") else ""),
        f"    {diff['significance_reason']}",
    ]
    for label in ("abilities", "talents"):
        c = diff[label]
        if not (c["added"] or c["removed"] or c["rank_changed"]):
            continue
        lines += ["", f"    {label}:"]
        for x in c["added"]:
            lines.append(f"      + {x['spell_id']} r{x['rank']}")
        for x in c["removed"]:
            lines.append(f"      - {x['spell_id']} r{x['rank']}")
        for x in c["rank_changed"]:
            lines.append(f"      ~ {x['spell_id']} rank {x['from']} -> {x['to']}")
    if diff["attribution"]:
        lines += ["", "    where the delta comes from:",
                  f"      {'ability':32}{'A':>10}{'B':>10}{'delta':>10}{'share':>8}"]
        for r in diff["attribution"]:
            share = (f"{r['share_of_delta_pct']:>7.0f}%"
                     if r.get("share_of_delta_pct") is not None else "      -")
            lines.append(
                f"      {r['name'][:31]:32}{r['damage_a']:>10,.0f}"
                f"{r['damage_b']:>10,.0f}{r['delta']:>+10,.0f}{share}")
    only = diff.get("warnings_only_on_one_side") or []
    if only:
        lines += ["", f"    ⚠ {len(only)} warning(s) fire on ONE SIDE ONLY — the "
                  "two builds are not equally well modelled:"]
        lines += [f"      * {w}" for w in only[:10]]
    return "\n".join(lines)


# --- HTML ----------------------------------------------------------------------

_CSS = """
:root { color-scheme: light dark; }
body { font: 14px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
       margin: 2rem auto; max-width: 60rem; padding: 0 1rem; }
h1, h2 { font-weight: 600; letter-spacing: -0.01em; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { text-align: right; padding: 0.3rem 0.6rem;
         border-bottom: 1px solid color-mix(in srgb, currentColor 15%, transparent); }
th:first-child, td:first-child { text-align: left; }
.bar { display: block; height: 0.5rem; border-radius: 2px;
       background: currentColor; opacity: 0.35; }
details { margin: 1rem 0; }
summary { cursor: pointer; font-weight: 600; }
li { margin: 0.25rem 0; }
.verdict { padding: 0.5rem 0.8rem; border-radius: 4px;
           border: 1px solid color-mix(in srgb, currentColor 25%, transparent); }
"""


def render_html(payload, title="Ascension sim report"):
    """A self-contained HTML page. No external assets, no scripts, no logic."""
    kind = payload.get("verdict") and "diff" or "sim"
    body = _html_diff(payload) if kind == "diff" else _html_sim(payload)
    return (f"<!doctype html><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{_CSS}</style>"
            f"<h1>{html.escape(title)}</h1>{body}")


def _rows(per_ability):
    total = sum(r.get("damage", 0.0) for r in per_ability.values()) or 1.0
    out = []
    for _sid, r in sorted(per_ability.items(),
                          key=lambda kv: -kv[1].get("damage", 0.0)):
        share = 100 * r.get("damage", 0.0) / total
        out.append(
            f"<tr><td>{html.escape(str(r.get('name')))}"
            + (" <small>(attributed)</small>" if r.get("attributed") else "")
            + f"</td><td>{r.get('casts', 0):.1f}</td>"
              f"<td>{r.get('damage', 0.0):,.0f}</td><td>{share:.1f}%</td>"
              f"<td style='width:30%'><span class='bar' "
              f"style='width:{share:.1f}%'></span></td></tr>")
    return "".join(out)


def _warnings_block(warnings):
    if not warnings:
        return ""
    items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings)
    return (f"<details><summary>{len(warnings)} warning(s) — every unvalidated "
            f"assumption this run made</summary><ul>{items}</ul></details>")


def _html_sim(d):
    return (
        f"<h2>{html.escape(d['tier'])} — {d['primary_value']:,.0f} "
        f"{html.escape(d['primary_metric'])}</h2>"
        f"<p>content: {html.escape(str(d.get('content_name')))}"
        + (f" · APL: {html.escape(str(d.get('apl_name')))}"
           if d.get("apl_name") else "") + "</p>"
        f"<table><thead><tr><th>ability</th><th>casts</th><th>damage</th>"
        f"<th>share</th><th></th></tr></thead><tbody>"
        f"{_rows(d['per_ability'])}</tbody></table>"
        + _warnings_block(d.get("warnings")))


def _html_diff(d):
    attr = "".join(
        f"<tr><td>{html.escape(r['name'])}</td><td>{r['damage_a']:,.0f}</td>"
        f"<td>{r['damage_b']:,.0f}</td><td>{r['delta']:+,.0f}</td></tr>"
        for r in d["attribution"])
    return (
        f"<div class='verdict'><strong>{html.escape(d['verdict'].upper())}</strong>"
        + (f" — {html.escape(d['winner'].upper())} wins" if d.get("winner") else "")
        + f"<br>{html.escape(d['significance_reason'])}</div>"
        f"<h2>A {d['dps_a']:,.0f} → B {d['dps_b']:,.0f} "
        f"({d['delta']:+,.0f})</h2>"
        f"<table><thead><tr><th>ability</th><th>A</th><th>B</th><th>delta</th>"
        f"</tr></thead><tbody>{attr}</tbody></table>"
        + _warnings_block(d.get("warnings_only_on_one_side")))


def _sim_result_dict(res):
    """SimResult -> plain dict. The dict IS the interface the renderers use."""
    return {
        "tier": getattr(res, "tier", "?"),
        "apl_name": getattr(res, "apl_name", None),
        "content_name": getattr(res, "content_name", None),
        "primary_metric": str(getattr(res, "primary_metric", "damage_done")),
        "primary_value": res.primary_value,
        "per_ability": res.per_ability,
        "warnings": list(res.warnings),
    }


def to_json(payload):
    return json.dumps(payload, indent=2, default=str)
