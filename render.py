"""Generate hidden-line orthographic and isometric views for every model.

build123d's own SVG exporter is not used here. It asserts start != end when
writing an elliptical arc, so any circular feature that projects to a full
ellipse -- most features in an isometric view -- crashes the export, and
halving the edges first does not reliably avoid it.

project_to_viewport already does the hard part: hidden-line removal, returning
visible and hidden edge lists that lie flat in the XY plane. Discretising those
into polylines and writing the SVG directly is a dozen lines and cannot hit
the exporter's degenerate cases.
"""

from __future__ import annotations

import importlib
from pathlib import Path

OUT = Path("out")
MODELS = ["bracket", "pulley", "transition", "leadscrew", "gearbox"]

# Camera direction and up-vector per view. The camera is placed along the
# direction at a distance scaled to the part (see main), because
# project_to_viewport projects from a *point*: a near camera gives a
# perspective view in which near features are magnified and the drawn extents
# no longer match the solid's bounding box. Pushing it far away makes the
# projection orthographic to within a fraction of a percent.
#
# The up-vector matters for the top view: the default (0,0,1) is parallel to
# the view direction there, leaving the roll undefined and the part drawn at
# an arbitrary angle.
VIEWS = {
    "iso": ((1, -1, 0.8), (0, 0, 1)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "side": ((1, 0, 0), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)),
}

# Dense assemblies get a reduced set; front and side add little over the
# isometric and cost the most to project.
VIEW_SUBSET = {"gearbox": ("iso", "top"), "gearbox_exploded": ("iso", "front")}

CAMERA_DISTANCE = 400.0   # multiples of the part's bounding-box diagonal

SAMPLES = 72          # points per curved edge
VISIBLE_W = 0.6
HIDDEN_W = 0.3
MARGIN = 0.06         # fraction of the larger dimension


def polyline(edge) -> list[tuple[float, float]]:
    """Sample an edge into 2D points. Straight edges need only their ends."""
    if str(edge.geom_type) == "GeomType.LINE":
        ts = (0.0, 1.0)
    else:
        ts = [i / SAMPLES for i in range(SAMPLES + 1)]
    pts = []
    for t in ts:
        v = edge @ t
        pts.append((v.X, v.Y))
    return pts


def to_svg(visible, hidden) -> str:
    """Emit one <path> per layer rather than one element per edge.

    Hidden-line projection of a gear returns an edge per profile segment --
    tens of thousands for a full gearbox. Writing each as its own <polyline>
    produced a 6 MB view. Concatenating them into a single path per layer, at
    a precision of 0.01 mm, gives the identical drawing an order of magnitude
    smaller and with two DOM nodes instead of thousands.
    """
    layers = [("hidden", hidden, HIDDEN_W), ("visible", visible, VISIBLE_W)]
    traced = [(name, [polyline(e) for e in edges], w) for name, edges, w in layers]

    xs = [p[0] for _, polys, _ in traced for poly in polys for p in poly]
    ys = [p[1] for _, polys, _ in traced for poly in polys for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = max(x1 - x0, y1 - y0) * MARGIN
    x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
    w, h = x1 - x0, y1 - y0

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {-y1:.2f} '
        f'{w:.2f} {h:.2f}" width="100%">',
        f'<rect x="{x0:.2f}" y="{-y1:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'fill="#ffffff"/>',
        '<g transform="scale(1,-1)" fill="none" stroke-linecap="round" '
        'stroke-linejoin="round">',
    ]
    for name, polys, width in traced:
        if not polys:
            continue
        segs = []
        for poly in polys:
            segs.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in poly))
        stroke = "#9aa0a6" if name == "hidden" else "#111111"
        dash = (
            f' stroke-dasharray="{width * 4:.2f} {width * 3:.2f}"'
            if name == "hidden"
            else ""
        )
        out.append(
            f'<path stroke="{stroke}" stroke-width="{width}"{dash} '
            f'd="{"".join(segs)}"/>'
        )
    out += ["</g>", "</svg>"]
    return "\n".join(out)


def views_for(part, stem: str) -> int:
    """Write one SVG per view for a single shape. Returns how many."""
    bb = part.bounding_box()
    reach = (bb.size.X**2 + bb.size.Y**2 + bb.size.Z**2) ** 0.5
    centre = bb.center()
    wanted = VIEW_SUBSET.get(stem, tuple(VIEWS))
    written = 0
    for view, (direction, up) in VIEWS.items():
        if view not in wanted:
            continue
        d = CAMERA_DISTANCE * reach
        origin = (
            centre.X + direction[0] * d,
            centre.Y + direction[1] * d,
            centre.Z + direction[2] * d,
        )
        visible, hidden = part.project_to_viewport(
            origin, viewport_up=up, look_at=centre
        )
        (OUT / f"{stem}_{view}.svg").write_text(
            to_svg(visible, hidden), encoding="utf-8"
        )
        written += 1
    return written


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name in MODELS:
        module = importlib.import_module(f"models.{name}")

        # Prefer a display-resolution build where the model offers one.
        maker = getattr(module, "build_display", module.build)
        variants = [(name, maker())]
        # An assembly also gets an exploded view, which is the only way to see
        # bodies that are hidden inside the housing when assembled.
        if hasattr(module, "exploded"):
            variants.append((f"{name}_exploded", module.exploded()))

        n = sum(views_for(shape, stem) for stem, shape in variants)
        print(f"{module.PART_ID} {module.TITLE}: {n} views")


if __name__ == "__main__":
    main()
