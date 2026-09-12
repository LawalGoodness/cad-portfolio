"""Build a single HTML page: drawing spec beside rendered result beside checks.

Generated from the models, so it cannot drift from what the code actually
produces.
"""

from __future__ import annotations

import html
import importlib
import re
from pathlib import Path

import cadkit

OUT = Path("out")
MODELS = ["bracket", "pulley", "transition", "leadscrew", "gearbox"]
VIEWS = ["iso", "front", "side", "top"]

# The gearbox is large and dense; four orthographic views of it would add
# megabytes to this page for little gain. The exploded isometric carries far
# more information than its front and side views do.
VIEW_OVERRIDE = {"gearbox": ["iso", "top", "exploded_iso", "exploded_front"]}

LABELS = {
    "iso": "Isometric", "front": "Front", "side": "Side", "top": "Top",
    "exploded_iso": "Exploded isometric", "exploded_front": "Exploded front",
}

CSS = """
:root{--bg:#f2f3f5;--card:#fff;--ink:#14161a;--dim:#5c6370;--line:#dcdfe4;
      --ok:#0a7d3f;--bad:#c0392b;--accent:#2b5fd9}
*{box-sizing:border-box}
body{margin:0;padding:28px;background:var(--bg);color:var(--ink);
     font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}
h1{font-size:24px;margin:0 0 4px}
p.lede{margin:0 0 26px;color:var(--dim);max-width:70ch}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;
        padding:20px;margin-bottom:22px}
h2{font-size:17px;margin:0 0 2px}
h2 span{color:var(--accent);font-family:ui-monospace,monospace;font-size:14px}
p.meta{margin:0 0 16px;color:var(--dim);font-size:13px}
.cols{display:grid;grid-template-columns:minmax(240px,1fr) minmax(300px,1.4fr)
      minmax(240px,1fr);gap:18px;align-items:start}
@media(max-width:1100px){.cols{grid-template-columns:1fr}}
h3{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--dim);
   margin:0 0 8px;font-weight:700}
pre.spec{margin:0;padding:12px;background:#f7f8fa;border:1px solid var(--line);
     border-radius:6px;font:12px/1.5 ui-monospace,monospace;white-space:pre-wrap;
     max-height:460px;overflow:auto}
.views{display:grid;grid-template-columns:1fr 1fr;gap:10px}
figure{margin:0;border:1px solid var(--line);border-radius:6px;padding:8px;
       background:#fff}
figcaption{font-size:10px;text-transform:uppercase;letter-spacing:.06em;
           color:var(--dim);margin-bottom:4px}
figure svg{display:block;width:100%;height:auto;max-height:190px}
table{border-collapse:collapse;width:100%;font-size:12px}
td{padding:3px 6px;border-bottom:1px solid var(--line);vertical-align:top}
td.k{white-space:nowrap;font-family:ui-monospace,monospace}
td.v{color:var(--dim)}
.pass{color:var(--ok);font-weight:700}.fail{color:var(--bad);font-weight:700}
.tally{margin-top:10px;font-size:12px;color:var(--dim)}
"""


def strip_svg(path: Path) -> str:
    t = path.read_text(encoding="utf-8")
    return re.sub(r'\s(width|height)="[^"]*"', "", t, count=2)


def main() -> None:
    parts = []
    grand_ok = grand_total = 0

    for name in MODELS:
        module = importlib.import_module(f"models.{name}")
        report, part = cadkit.acceptance(module)
        ok = len(report.rows) - report.n_failed
        grand_ok += ok
        grand_total += len(report.rows)

        spec_file = next(Path("drawings").glob(f"{module.PART_ID}*.md"))
        spec = html.escape(spec_file.read_text(encoding="utf-8"))

        views = "".join(
            f'<figure><figcaption>{LABELS[v]}</figcaption>'
            f'{strip_svg(OUT / f"{name}_{v}.svg")}</figure>'
            for v in VIEW_OVERRIDE.get(name, VIEWS)
            if (OUT / f"{name}_{v}.svg").exists()
        )

        rows = "".join(
            f'<tr><td class="k">{html.escape(n)}</td>'
            f'<td class="{"pass" if o else "fail"}">{"PASS" if o else "FAIL"}</td>'
            f'<td class="v">{html.escape(d)}</td></tr>'
            for n, o, d in report.rows
        )

        mass = part.volume * module.DENSITY
        n_solids = len(part.solids())
        body_note = f" &middot; {n_solids} bodies" if n_solids > 1 else ""
        parts.append(f"""<section>
<h2><span>{module.PART_ID}</span> &nbsp;{html.escape(module.TITLE)}</h2>
<p class="meta">{html.escape(module.MATERIAL)} &middot;
 {part.volume:,.0f} mm&sup3; &middot; {mass:,.0f} g &middot;
 {len(part.faces()):,} faces{body_note}</p>
<div class="cols">
  <div><h3>Drawing supplied</h3><pre class="spec">{spec}</pre></div>
  <div><h3>Model produced</h3><div class="views">{views}</div></div>
  <div><h3>Acceptance checks</h3><table>{rows}</table>
       <p class="tally">{ok} of {len(report.rows)} passed</p></div>
</div></section>""")

    page = f"""<title>Programmatic CAD Portfolio</title>
<style>{CSS}</style>
<h1>Programmatic CAD portfolio</h1>
<p class="lede">Five mechanical parts, each specified as a dimensioned drawing,
modelled entirely in Python with build123d, exported to STEP, and verified
against the drawing by an automated acceptance battery. The last is a working
six-body planetary gearbox whose involute teeth are generated from the involute
equation, and whose meshing pairs are proven not to interfere by boolean
intersection.
<strong>{grand_ok} of {grand_total} checks passing.</strong>
Views are hidden-line projections generated from the solids themselves, not
screenshots of a CAD GUI.</p>
{"".join(parts)}"""

    Path("index.html").write_text(page, encoding="utf-8")
    print(f"index.html written: {grand_ok}/{grand_total} checks")


if __name__ == "__main__":
    main()
