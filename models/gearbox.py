"""DRW-005 Planetary Gearbox -- 6-body assembly, 3.5:1 reduction.

A working epicyclic gear train: sun, three planets, internal ring gear, and a
carrier that both locates the planets and carries the output. Every tooth flank
is a true involute generated from the involute equation in gears.py.

Three things make this an assembly problem rather than six modelling problems.

**The tooth counts are not free.** For the planets to sit between sun and ring
at all, z_ring = z_sun + 2*z_planet. For three planets to sit at 120 degree
spacing and all mesh simultaneously, (z_sun + z_ring) / n_planets must be a
whole number. 24, 18, 60 and three planets satisfies both: 60 = 24 + 2*18, and
(24 + 60)/3 = 28. Change the sun to 25 teeth and the gearbox cannot be
assembled, however good each individual gear is.

**Each planet needs its own clocking.** A planet dropped in at an arbitrary
rotation will not mesh. It needs a tooth space facing the sun along the line of
centres. Because the planet has an even tooth count, that same condition puts a
space on the outward side too, which is what lets the ring tooth enter. The
required phase is derived in build() rather than found by trial.

**Correctness is checkable without looking.** Two gears that mesh correctly
touch but never share volume, so a boolean intersection between any meshing
pair must come back empty. That is the check that would catch a wrong pressure
angle, a wrong centre distance, or a mis-clocked planet -- none of which a
rendered image reliably shows.
"""

from __future__ import annotations

import math

from build123d import *

import gears

PART_ID = "DRW-005"
TITLE = "Planetary Gearbox, 3.5:1"
MATERIAL = "C45 steel"
DENSITY = 7.85e-3  # g/mm3

# --- Gear set (mm) ----------------------------------------------------------
MODULE = 2.0
Z_SUN = 24
Z_PLANET = 18
Z_RING = Z_SUN + 2 * Z_PLANET          # 60, forced by the geometry
N_PLANETS = 3
BACKLASH = 0.05

FACE_WIDTH = 12.0
CENTRE_DISTANCE = MODULE * (Z_SUN + Z_PLANET) / 2      # 42.0
RATIO = 1 + Z_RING / Z_SUN                              # 3.5, ring fixed

# --- Housing and shafts -----------------------------------------------------
RING_OD = 144.0
RING_BOLT_D = 6.0
RING_BOLT_PCD = 132.0
RING_BOLT_N = 6

SUN_BORE = 12.0
PLANET_BORE = 10.0
PIN_D = 9.8                 # clearance fit in the planet bore
PIN_TOP = FACE_WIDTH + 1.0
CARRIER_OD = 96.0
CARRIER_T = 8.0
CARRIER_Z = -10.0           # underside of the carrier plate
OUTPUT_OD = 16.0
OUTPUT_BORE = 14.0          # hollow, so the sun shaft passes through
OUTPUT_BOTTOM = -26.0

EXPECT = {
    "bbox": (RING_OD, RING_OD, PIN_TOP - OUTPUT_BOTTOM),
    "volume": 170459.3,     # sum of all five bodies
    "volume_tol": 0.05,
    "com": (0.0, 0.0, None),
    "com_tol": 0.20,
    "solids": 1 + N_PLANETS + 1 + 1,    # sun, planets, ring, carrier
}


# Flank sampling. The exact set is what gets validated and exported; the
# coarse set exists only for drawing views. Hidden-line removal is superlinear
# in edge count, and at full resolution the assembly carries about 15,000
# edges -- one isometric view took over nine minutes. Coarsening the flanks
# for display alone cuts that by roughly an order of magnitude without
# touching the geometry that any check or STEP file sees.
EXACT_STEPS = dict(flank_steps=14, tip_steps=3, root_steps=4)
DISPLAY_STEPS = dict(flank_steps=4, tip_steps=1, root_steps=1)


def _gear_face(z: int, internal: bool, phase: float, steps=None):
    """A closed face for one gear profile, ready to extrude."""
    pts = gears.gear_profile(z, MODULE, internal=internal, backlash=BACKLASH,
                             phase=phase, **(steps or EXACT_STEPS))
    with BuildLine() as wire:
        Polyline(*pts, close=True)
    return make_face(wire.line)


def _planet_phase(psi: float) -> float:
    """Clocking that puts a tooth space on the line of centres.

    Tooth centres of the generated profile sit at phase + 2*pi*k/z, so spaces
    sit half a pitch further round, at phase + pi/z + 2*pi*k/z. Requiring a
    space to point back at the sun -- direction psi + pi from the planet's own
    centre -- and taking k = 0 gives the expression below.
    """
    return psi + math.pi - math.pi / Z_PLANET


def build_bodies(steps=None) -> dict[str, Part]:
    """Every body of the assembly, positioned in its assembled location."""
    bodies: dict[str, Part] = {}

    # Sun -------------------------------------------------------------------
    with BuildPart() as sun:
        with BuildSketch(Plane.XY):
            add(_gear_face(Z_SUN, False, 0.0, steps))
            Circle(SUN_BORE / 2, mode=Mode.SUBTRACT)
        extrude(amount=FACE_WIDTH)
    bodies["sun"] = sun.part

    # Planets ---------------------------------------------------------------
    for i in range(N_PLANETS):
        psi = 2 * math.pi * i / N_PLANETS
        with BuildPart() as planet:
            with BuildSketch(Plane.XY):
                add(_gear_face(Z_PLANET, False, _planet_phase(psi), steps))
                Circle(PLANET_BORE / 2, mode=Mode.SUBTRACT)
            extrude(amount=FACE_WIDTH)
        bodies[f"planet{i + 1}"] = planet.part.translate(
            (CENTRE_DISTANCE * math.cos(psi), CENTRE_DISTANCE * math.sin(psi), 0)
        )

    # Ring: an annulus with the toothed bore cut out of it -------------------
    with BuildPart() as ring:
        with BuildSketch(Plane.XY):
            Circle(RING_OD / 2)
            add(_gear_face(Z_RING, True, 0.0, steps), mode=Mode.SUBTRACT)
        extrude(amount=FACE_WIDTH)
        with BuildSketch(Plane.XY):
            with PolarLocations(RING_BOLT_PCD / 2, RING_BOLT_N):
                Circle(RING_BOLT_D / 2)
        extrude(amount=FACE_WIDTH, mode=Mode.SUBTRACT)
    bodies["ring"] = ring.part

    # Carrier: plate, three planet pins, hollow output shaft -----------------
    with BuildPart() as carrier:
        with Locations((0, 0, CARRIER_Z)):
            Cylinder(CARRIER_OD / 2, CARRIER_T,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))

        for i in range(N_PLANETS):
            psi = 2 * math.pi * i / N_PLANETS
            x = CENTRE_DISTANCE * math.cos(psi)
            y = CENTRE_DISTANCE * math.sin(psi)
            with Locations((x, y, CARRIER_Z + CARRIER_T)):
                Cylinder(PIN_D / 2, PIN_TOP - (CARRIER_Z + CARRIER_T),
                         align=(Align.CENTER, Align.CENTER, Align.MIN))

        with Locations((0, 0, OUTPUT_BOTTOM)):
            Cylinder(OUTPUT_OD / 2, CARRIER_Z - OUTPUT_BOTTOM,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Through bore for the sun shaft
        with BuildSketch(Plane.XY.offset(OUTPUT_BOTTOM)):
            Circle(OUTPUT_BORE / 2)
        extrude(amount=CARRIER_Z + CARRIER_T - OUTPUT_BOTTOM, mode=Mode.SUBTRACT)
    bodies["carrier"] = carrier.part

    return bodies


def build() -> Compound:
    """The assembled gearbox as one compound of six solids."""
    return Compound(children=list(build_bodies().values()))


def build_display() -> Compound:
    """Same assembly at drawing resolution. Used by render.py only."""
    return Compound(children=list(build_bodies(DISPLAY_STEPS).values()))


def exploded(gap: float = 46.0) -> Compound:
    """The same assembly pulled apart along Z, for a legible portfolio view.

    Bodies are separated in the order they go together, so the picture reads
    as an assembly sequence rather than an arbitrary scatter.
    """
    bodies = build_bodies(DISPLAY_STEPS)
    lift = {"ring": 0.0, "sun": gap, "carrier": -gap}
    for i in range(N_PLANETS):
        lift[f"planet{i + 1}"] = 2 * gap
    return Compound(
        children=[b.translate((0, 0, lift[n])) for n, b in bodies.items()]
    )


def extra_checks(_assembly) -> list[tuple[str, bool, str]]:
    """Assembly-level correctness: tooth counts, ratio, and interference."""
    rows: list[tuple[str, bool, str]] = []

    rows.append((
        "mesh condition",
        Z_RING == Z_SUN + 2 * Z_PLANET,
        f"z_ring {Z_RING} == z_sun {Z_SUN} + 2*z_planet {Z_PLANET}",
    ))
    assembly_number = (Z_SUN + Z_RING) / N_PLANETS
    rows.append((
        "assembly condition",
        abs(assembly_number - round(assembly_number)) < 1e-9,
        f"(z_sun + z_ring)/n = {assembly_number:g}, must be integer",
    ))
    rows.append((
        "gear ratio",
        abs(RATIO - 3.5) < 1e-9,
        f"1 + z_ring/z_sun = {RATIO:g}:1, ring fixed",
    ))

    bodies = build_bodies()
    pairs = [("sun", f"planet{i + 1}") for i in range(N_PLANETS)]
    pairs += [(f"planet{i + 1}", "ring") for i in range(N_PLANETS)]
    pairs += [(f"planet{i + 1}", "carrier") for i in range(N_PLANETS)]

    for a, b in pairs:
        overlap = (bodies[a] & bodies[b]).volume
        rows.append((
            f"clear {a}/{b}",
            overlap < 1e-6,
            f"shared volume {overlap:.3e} mm3",
        ))

    return rows


if __name__ == "__main__":
    bodies = build_bodies()
    total = 0.0
    for name, body in bodies.items():
        print(f"{name:9} vol {body.volume:10,.1f} mm3  faces {len(body.faces()):4}")
        total += body.volume
    print(f"{'TOTAL':9} vol {total:10,.1f} mm3  mass {total * DENSITY:,.0f} g")
    print(f"ratio {RATIO}:1   centre distance {CENTRE_DISTANCE} mm")
    for name, ok, detail in extra_checks(None):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22} {detail}")
