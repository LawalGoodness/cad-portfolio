# DRW-004 — Tr24x5 Lead Screw

Material: C45 steel, density 7.85 g/cm3
All dimensions in millimetres. Tolerance +/-0.1 unless noted.

## Datums
- Datum A: threaded end, Z = 0
- Datum B: screw axis, X = Y = 0

## Thread
- ISO 2904 trapezoidal, Tr24x5, single start, right hand
- Major diameter 24.0, pitch 5.0, 16 full turns
- Thread height H4 = 2.75 (0.5P + ac, ac = 0.25)
- Minor diameter 18.5
- Flank angle 30 deg included
- Threaded length 80.0 from Datum A
- Cut as a swept trapezoidal groove, not a library primitive

## Shank
- Diameter 20.0, length 25.0, from Z = 80.0 to Z = 105.0
- Chamfer 2.0 x 45 deg at the free end
- Cross hole diameter 6.0 through, axis on Y, at Z = 92.5

## Acceptance criteria
- Single watertight solid
- Volume 35973 mm3 +/- 5%; an unthreaded blank is 44045 mm3
- Exactly 29 faces. This is the check that catches a sweep which
  silently subtracts nothing, since the volume check alone will not.
- Bounding box 24.0 x 24.0 x 105.0 (+/-0.1)
- Cylindrical faces present at R3.0, R10.0 and R12.0. The cross hole has
  no circular edge: it meets the round shank on a Steinmetz curve.
