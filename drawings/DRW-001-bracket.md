# DRW-001 — Pillow Block Bearing Bracket

Material: 6061-T6 aluminium, density 2.70 g/cm3
All dimensions in millimetres. Tolerance +/-0.1 unless noted.

## Datums
- Datum A: underside of base plate, Z = 0
- Datum B: longitudinal centreline, X = 0
- Datum C: transverse centreline, Y = 0

## Base plate
- Footprint 90.0 x 50.0, corner radius R8.0
- Thickness 12.0, extruded +Z from Datum A

## Mounting holes (2x)
- Through holes dia 9.0, axes parallel to Z
- Located at X = +/-32.0, Y = 0.0
- Counterbore dia 15.0 x 5.0 deep, from top face (Z = 12.0)

## Bearing hub
- Cylindrical, axis parallel to Y, passing through X = 0.0, Z = 52.0
- Outer dia 46.0, overall length 40.0, symmetric about Datum C
- Through bore dia 28.0, coaxial with hub
- Bore chamfer 1.5 x 45 deg, both ends

## Support web
- Lofted transition, base cross-section 44.0 (X) x 30.0 (Y) at Z = 12.0
- Upper cross-section 26.0 (X) x 30.0 (Y) at Z = 36.0
- Upper face terminates inside the hub envelope and below the bore,
  so no web face is coplanar with a hub end face

## Fillets
- R4.0 where web meets base top face

## Acceptance criteria
- Single watertight solid, 26 faces / 58 edges
- Volume 112993 mm3 +/- 4%
- Bounding box 90.0 x 50.0 x 75.0 (+/-0.1)
- Centre of mass on X = 0 and Y = 0 (+/-0.05)
- Exported as ISO 10303-21 STEP AP214
