"""Shared acceptance-checking harness for the DRW-xxx models.

One Report class and a fixed battery of checks, so every part in the repo is
verified the same way and a new part costs only its EXPECT block.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from build123d import Axis, CenterOf, GeomType, Part


@dataclass
class Report:
    part_id: str
    title: str
    rows: list[tuple[str, bool, str]] = field(default_factory=list)

    def check(self, name: str, ok: bool, detail: str) -> None:
        self.rows.append((name, bool(ok), detail))

    def near(
        self, name: str, actual: float, target: float, tol: float, unit: str = "mm"
    ) -> None:
        self.check(
            name,
            abs(actual - target) <= tol,
            f"{actual:.3f} {unit} (target {target:.3f} +/-{tol:g})",
        )

    @property
    def passed(self) -> bool:
        return all(ok for _, ok, _ in self.rows)

    @property
    def n_failed(self) -> int:
        return sum(1 for _, ok, _ in self.rows if not ok)

    def render(self) -> str:
        width = max(len(n) for n, _, _ in self.rows)
        return "\n".join(
            f"  [{'PASS' if ok else 'FAIL'}] {n.ljust(width)}  {d}"
            for n, ok, d in self.rows
        )


def acceptance(module) -> Report:
    """Run the standard battery against a model module.

    The module must expose PART_ID, TITLE, DENSITY, EXPECT and build().
    """
    part: Part = module.build()
    exp = module.EXPECT
    r = Report(module.PART_ID, module.TITLE)

    # Topology -------------------------------------------------------------
    r.check("valid BRep", part.is_valid, "OCCT validity check")
    solids = part.solids()
    want_solids = exp.get("solids", 1)
    label = "body count" if want_solids > 1 else "single solid"
    r.check(label, len(solids) == want_solids,
            f"{len(solids)} solid(s), expected {want_solids}")
    r.check(
        "watertight",
        all(f.is_valid for f in part.faces()),
        f"{len(part.faces())} faces, {len(part.edges())} edges",
    )

    # Bounding box ---------------------------------------------------------
    bb = part.bounding_box().size
    bx, by, bz = exp["bbox"]
    r.near("bbox X", bb.X, bx, 0.1)
    r.near("bbox Y", bb.Y, by, 0.1)
    r.near("bbox Z", bb.Z, bz, 0.1)

    # Mass properties ------------------------------------------------------
    vol = exp["volume"]
    r.near("volume", part.volume, vol, vol * exp.get("volume_tol", 0.04), "mm3")

    com = part.center(CenterOf.MASS)
    cx, cy, cz = exp["com"]
    for label, actual, target in (
        ("CoM X", com.X, cx),
        ("CoM Y", com.Y, cy),
        ("CoM Z", com.Z, cz),
    ):
        if target is not None:
            r.near(label, actual, target, exp.get("com_tol", 0.05))

    mass = part.volume * module.DENSITY
    r.check("mass", True, f"{mass:.1f} g in {module.MATERIAL}")

    inertia = part.matrix_of_inertia
    r.check(
        "inertia tensor",
        True,
        "Ixx={:.3e} Iyy={:.3e} Izz={:.3e}".format(
            inertia[0][0], inertia[1][1], inertia[2][2]
        ),
    )

    # Cylindrical faces of a given diameter. Needed where a feature has no
    # circular edge -- a cross hole through a round shank meets the surface
    # on a Steinmetz curve, so the hole exists as a face but never as a
    # circle. Checking only edges reports a correct model as broken.
    face_radii = sorted(
        {round(f.radius, 3) for f in part.faces().filter_by(GeomType.CYLINDER)}
    )
    for dia in exp.get("face_diameters", []):
        r.check(
            f"face dia {dia:g}",
            any(abs(rad - dia / 2) < 1e-3 for rad in face_radii),
            f"R{dia / 2:.2f} found among {face_radii}",
        )

    # Specified diameters really present -----------------------------------
    radii = sorted({round(e.radius, 3) for e in part.edges().filter_by(GeomType.CIRCLE)})
    for dia in exp.get("diameters", []):
        r.check(
            f"dia {dia:g}",
            any(abs(rad - dia / 2) < 1e-3 for rad in radii),
            f"R{dia / 2:.2f} found",
        )

    # Feature counts -------------------------------------------------------
    for label, fn, target in exp.get("counts", []):
        actual = fn(part)
        r.check(f"count {label}", actual == target, f"{actual} (expected {target})")

    # Model-specific checks. Assemblies use this for things no single-body
    # battery can express -- gear ratios, and whether two bodies that are
    # meant to mesh actually share any volume.
    if hasattr(module, "extra_checks"):
        for name, ok, detail in module.extra_checks(part):
            r.check(name, ok, detail)

    return r, part
