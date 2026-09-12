# Programmatic CAD portfolio

Five mechanical parts, each specified as a dimensioned drawing, modelled entirely in
Python on the OpenCascade kernel, exported to STEP, and verified against the drawing by
an automated acceptance battery.

**80 of 80 checks passing.** STEP files are written only for parts that pass cleanly, and
the runner exits non-zero on failure so it drops straight into CI.

| ID | Part | Bodies | Demonstrates |
|---|---|---|---|
| DRW-001 | Pillow block bearing bracket | 1 | Loft, fillet, chamfer, counterbored holes |
| DRW-002 | V-belt pulley, SPZ | 1 | Revolve of a profile, polar pattern, keyway |
| DRW-003 | Square-to-round transition duct | 1 | Loft between dissimilar sections, shelling |
| DRW-004 | Tr24x5 lead screw | 1 | Helical sweep with a Frenet frame |
| DRW-005 | **Planetary gearbox, 3.5:1** | **6** | **Involute gear generation, assembly, interference** |

## Layout

```
drawings/     DRW-001..005, the dimensioned specs, written before the models
models/       one module per part, each exposing build() and EXPECT
gears.py      involute tooth profile generation from first principles
cadkit.py     the shared acceptance battery
validate.py   runs every model, writes STEP on a clean pass
render.py     hidden-line orthographic and isometric views
sheet.py      builds index.html, the portfolio page
out/          STEP files and SVG views
```

## Running it

```
C:\cadvenv\Scripts\python.exe validate.py
```

A virtual environment at a short path is required rather than the Microsoft Store Python:
OCP's nested dependency paths exceed the Windows 260-character limit under
`...\Packages\PythonSoftwareFoundation.Python.3.13_...\LocalCache\`, and the install fails
part-way with an `OSError`.

## Results

```
PART     NAME                                 CHECKS   VOLUME mm3   MASS g
DRW-001  Pillow Block Bearing Bracket          15/15      112,993      305
DRW-002  V-Belt Pulley                         15/15      220,570     1588
DRW-003  Square-to-Round Transition Duct       12/12      315,073     2473
DRW-004  Tr24x5 Lead Screw                     15/15       35,973      282
DRW-005  Planetary Gearbox, 3.5:1              23/23      170,459     1338
```

---

## DRW-005 — the planetary gearbox

A working epicyclic train: sun (24 teeth), three planets (18), internal ring (60), and a
carrier that locates the planets and takes the output. Ring fixed, sun in, carrier out,
**3.5:1 reduction**.

Every tooth flank is a true **involute**, generated from the involute equation in
`gears.py` rather than imported from a gear library. The involute is used because it is
the only profile that transmits a constant angular velocity ratio regardless of small
errors in centre distance; an arc approximation gives a gear that turns but with velocity
ripple and no calculable contact ratio.

Three things make this an assembly problem rather than six modelling problems.

**The tooth counts are not free.** For planets to fit between sun and ring at all,
`z_ring = z_sun + 2·z_planet`. For three planets to sit at 120° and all mesh at once,
`(z_sun + z_ring) / n_planets` must be a whole number. 24/18/60 with three planets
satisfies both: `60 = 24 + 2·18`, and `84/3 = 28`. A 25-tooth sun makes the gearbox
unassemblable no matter how good each individual gear is.

**Each planet needs its own clocking.** A planet dropped in at an arbitrary rotation will
not mesh; it needs a tooth *space* on the line of centres facing the sun. Since the
generator places tooth centres at `phase + 2πk/z`, the required phase for a planet at
carrier angle ψ is `ψ + π − π/z_planet`. Because the planet tooth count is even, that
same condition puts a space on the outward side too, which is what lets the ring tooth
enter.

**Correctness is checkable without looking at it.** Correctly meshing involute gears touch
but never share volume, so a boolean intersection of any meshing pair must be empty:

```
[PASS] clear sun/planet1      shared volume 0.000e+00 mm3
[PASS] clear planet1/ring     shared volume 0.000e+00 mm3
   ... 12 pairs, every one exactly zero
```

That single check would catch a wrong pressure angle, a wrong centre distance, or a
mis-clocked planet — none of which a rendered image shows reliably.

---

## The six failures worth reading about

Each of these is a real failure that happened during the build, and each one changed
either the model or the harness.

### 1. Coplanar faces block a chamfer — DRW-001

`chamfer()` failed with `StdFail_NotDone`. The support web was specified the same depth in
Y as the hub length, making their end faces coplanar, so the bore's end edge was split
across two surfaces instead of being one circle. Reducing the web from 40 to 30 mm and
terminating it below the bore fixed it. Interactive CAD hides this class of problem behind
a dialog; in code it surfaces as an exception you have to reason about topologically.

### 2. Operation order breaks a chamfer — DRW-002

Chamfering the bore *after* cutting the keyway fails outright: the bore end edge is then an
arc bounded by three faces, and OCCT's chamfer builder handles two. Chamfering first
succeeded but left an invalid conical face once the keyway sliced it. The fix was to turn
the chamfer as part of the revolved profile — which is what a lathe does anyway.

### 3. The wrong offset variant — DRW-003

Shelling the lofted duct failed with `Kind.INTERSECTION`, which extends adjacent offset
faces until they meet and has no solution where the ruled surface changes curvature sign.
`Kind.ARC` rolls a fillet across that junction and succeeds. Determined by testing each
variant in a minimal script rather than guessing.

### 4. A sweep that silently did nothing — DRW-004

The thread sweep subtracted nothing at all. No exception. The volume came back at
44,045 mm³ — exactly an unthreaded blank — which a loose volume tolerance would have
passed. Only the face count betrayed it: 7 where a threaded screw has 29.

The cause was creating the shank inside a `Locations` context before the sweep, leaving
the builder with no pending faces to consume. Cutting the thread on a clean blank first
and adding the shank after fixed it, and matches the real machining order. **The face
count is now a permanent check**, so that specific silent failure can never pass again.

### 5. A validator that was wrong, not the model — DRW-004

The Ø6 cross-hole check failed on a perfectly good model. A hole through a *round* shank
meets the surface on a Steinmetz curve, not a circle, so the feature exists as a
cylindrical face and never as a circular edge. The harness gained a `face_diameters` check.
A failing check is a hypothesis, not a verdict.

### 6. Perspective distortion in the views — render.py

`project_to_viewport` projects from a point, so a near camera gives a perspective view in
which near features are magnified. The drawn extents disagreed with the solids' bounding
boxes by up to 36%. The camera is now placed at 400 bounding-box diagonals, making the
projection orthographic to within a fraction of a percent, and the top view needed an
explicit up-vector because the default is parallel to its view direction. Every view is
now verified against its solid to **0.00%**.

---

## Why the harness matters more than the models

A STEP file that opens is not a STEP file that is correct. `cadkit.py` asserts topology
(valid BRep, expected body count, watertightness), dimensions (bounding box, specified
diameters as edges *or* cylindrical faces), physical properties (volume, centre of mass,
inertia tensor), feature counts, and — for assemblies — model-specific checks like gear
ratios and pairwise interference.

Failure 4 is the argument for all of it. The model was wrong, the volume check passed, and
a human looking at a render would have seen a screw-shaped object. Only an assertion
about topology caught it.

## A note on display resolution

Hidden-line removal is superlinear in edge count. At full flank resolution the gearbox
carries about 15,000 edges and a single isometric view took over nine minutes. `render.py`
uses a coarser flank sampling for drawings only — 4,659 edges, and all four views in 21
seconds. Validation and STEP export always use the exact geometry; the reduced set never
reaches a check or an exported file.

## Live portfolio

https://lawalgoodness.github.io/cad-portfolio/
