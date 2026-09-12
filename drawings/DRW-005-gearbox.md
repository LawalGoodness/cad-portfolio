# DRW-005 — Planetary Gearbox, 3.5:1

Material: C45 steel, density 7.85 g/cm3
All dimensions in millimetres. Six bodies, shown assembled.

## Gear set
- Module 2.0, pressure angle 20 deg, involute profile per ISO 53
- Sun: 24 teeth, pitch dia 48.0, external
- Planet: 18 teeth, pitch dia 36.0, external, 3 off at 120 deg
- Ring: 60 teeth, pitch dia 120.0, internal
- Face width 12.0, common to all gears
- Backlash 0.05 circumferential at the pitch circle
- Addendum 1.0 x module, dedendum 1.25 x module

## Kinematic constraints
These are not free choices. Both must hold or the unit cannot be assembled:
- Meshing:  z_ring = z_sun + 2 x z_planet  ->  60 = 24 + 2 x 18
- Assembly: (z_sun + z_ring) / n_planets must be a whole number  ->  84 / 3 = 28
- Centre distance sun to planet: m x (z_sun + z_planet) / 2 = 42.0
- Ratio, ring fixed, sun input, carrier output: 1 + z_ring / z_sun = 3.5:1

## Planet clocking
Each planet must be rotated so a tooth space lies on the line of centres facing
the sun. With the profile generator placing tooth centres at
phase + 2*pi*k/z, the required phase for a planet at carrier angle psi is:

    phase = psi + pi - pi / z_planet

Because the planet tooth count is even, this simultaneously places a space on
the outward side, which is what allows the ring tooth to enter.

## Ring gear body
- Outside diameter 144.0, face width 12.0
- Tip diameter 116.0 (inner), root diameter 125.0
- 6 x dia 6.0 mounting holes on 132.0 PCD

## Carrier
- Plate dia 96.0 x 8.0 thick, underside at Z = -10.0
- 3 x planet pins dia 9.8, from plate top to Z = +13.0
- Output shaft dia 16.0 from Z = -26.0 to the plate
- Through bore dia 14.0 so the sun shaft passes down the output shaft

## Shaft bores
- Sun bore dia 12.0
- Planet bore dia 10.0, giving 0.2 clearance on the 9.8 pins

## Acceptance criteria
- 6 valid solids: sun, 3 planets, ring, carrier
- Total volume 170459 mm3 +/- 5%, mass 1338 g in C45
- Bounding box 144.0 x 144.0 x 39.0 (+/-0.1)
- Centre of mass on X = 0 and Y = 0 (+/-0.2)
- Meshing, assembly and ratio conditions above all satisfied
- **Zero interference.** Boolean intersection of every meshing pair must have
  zero volume: sun to each planet, each planet to ring, each planet to its
  carrier pin. Correctly meshing involute gears touch but never share volume,
  so any non-zero result indicates a wrong pressure angle, a wrong centre
  distance, or a mis-clocked planet — none of which a rendered image shows
  reliably.
