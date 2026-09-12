"""DRW-004 Tr24x5 Lead Screw -- helical sweep, plain shank, cross hole.

The thread is not a library primitive. It is a trapezoidal groove profile
swept along a Helix and subtracted from the blank, which is the operation a
single-point threading tool actually performs.

Two details that decide whether this works:

1. The profile plane is built as Plane(origin=path@0, x_dir=(1,0,0),
   z_dir=path%0). The helix tangent at t=0 has no X component, so the radial
   direction (1,0,0) is guaranteed perpendicular to it and local sketch X is
   truly radial. Letting build123d pick x_dir gives an arbitrary roll and the
   flank angles come out wrong.

2. is_frenet=True. The Frenet frame keeps the profile's orientation tied to
   the path's curvature instead of letting it rotate freely, which here is
   the difference between 16 faces and 18 with a subtly twisted flank.
"""

from __future__ import annotations

import math

from build123d import *

PART_ID = "DRW-004"
TITLE = "Tr24x5 Lead Screw"
MATERIAL = "C45 steel"
DENSITY = 7.85e-3  # g/mm3

# --- Drawing constants (mm) -------------------------------------------------
MAJOR_D = 24.0
PITCH = 5.0
THREAD_LEN = 80.0

FLANK_ANGLE = 30.0          # included, ISO 2904 trapezoidal
CLEARANCE = 0.25
THREAD_DEPTH = 0.5 * PITCH + CLEARANCE      # H4 = 2.75
MINOR_D = MAJOR_D - 2 * THREAD_DEPTH        # 18.5

SHANK_D = 20.0
SHANK_LEN = 25.0
SHANK_CHAMFER = 2.0

CROSS_HOLE_D = 6.0
CROSS_HOLE_Z = THREAD_LEN + SHANK_LEN / 2

OVERALL = THREAD_LEN + SHANK_LEN

# Trapezoidal groove, measured in the plane normal to the helix.
# Tooth thickness at the pitch line is P/2; the groove is therefore also P/2
# there and opens out towards the crest at the flank angle.
_TAN_FLANK = math.tan(math.radians(FLANK_ANGLE / 2))
_PITCH_R = (MAJOR_D + MINOR_D) / 4
_DR = MAJOR_D / 2 - _PITCH_R                      # pitch line to crest
_HALF_AT_CREST = PITCH / 4 + _DR * _TAN_FLANK
_HALF_AT_ROOT = PITCH / 4 - _DR * _TAN_FLANK
_OVERCUT = 1.0                                    # ensure the crest is cleared
_HALF_OVERCUT = _HALF_AT_CREST + _OVERCUT * _TAN_FLANK

EXPECT = {
    "bbox": (MAJOR_D, MAJOR_D, OVERALL),
    "volume": 35972.9,   # as-designed, thread cut by helical sweep
    "volume_tol": 0.05,
    "com": (0.0, 0.0, None),
    "com_tol": 0.15,
    "face_diameters": [CROSS_HOLE_D, SHANK_D, MAJOR_D],
    # Guards the silent-no-op failure described in build(): an uncut blank
    # has 5 faces and a volume of 44045 mm3, both of which pass a loose
    # volume check on their own. The face count is what actually catches it.
    "counts": [("faces", lambda p: len(p.faces()), 29)],
}


def build() -> Part:
    # Thread the blank first, then add the shank.
    #
    # This order is not cosmetic. sweep() consumes the builder's pending
    # faces, and creating the shank inside a Locations context beforehand
    # leaves the builder in a state where the sweep silently subtracts
    # nothing: the volume comes back exactly equal to the unthreaded blank
    # and only a face count betrays it. Cutting the thread on a clean blank
    # avoids that, and matches how the part is actually made -- turn and
    # thread the bar, then machine the shank down.
    with BuildPart() as blank:
        Cylinder(
            MAJOR_D / 2, THREAD_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        path = Helix(PITCH, THREAD_LEN, MAJOR_D / 2)
        with BuildSketch(Plane(origin=path @ 0, x_dir=(1, 0, 0), z_dir=path % 0)):
            with BuildLine():
                Polyline(
                    (_OVERCUT, -_HALF_OVERCUT),
                    (_OVERCUT, _HALF_OVERCUT),
                    (-THREAD_DEPTH, _HALF_AT_ROOT),
                    (-THREAD_DEPTH, -_HALF_AT_ROOT),
                    close=True,
                )
            make_face()
        sweep(path=path, is_frenet=True, mode=Mode.SUBTRACT)

    with BuildPart() as screw:
        add(blank.part)

        with Locations((0, 0, THREAD_LEN)):
            Cylinder(
                SHANK_D / 2, SHANK_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )

        # Cross hole through the shank ----------------------------------------
        with BuildSketch(Plane.XZ):
            with Locations((0, CROSS_HOLE_Z)):
                Circle(CROSS_HOLE_D / 2)
        extrude(amount=SHANK_D, both=True, mode=Mode.SUBTRACT)

        # Chamfer the free end of the shank -----------------------------------
        top = screw.faces().filter_by(Plane.XY).group_by(Axis.Z)[-1][0]
        chamfer(top.edges(), SHANK_CHAMFER)

    return screw.part


if __name__ == "__main__":
    p = build()
    bb = p.bounding_box()
    print(f"volume {p.volume:.1f} mm3  bbox {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}")
    print(f"solids {len(p.solids())}  faces {len(p.faces())}  mass {p.volume*DENSITY:.1f} g")
    print(f"minor dia {MINOR_D}  turns {THREAD_LEN/PITCH:.0f}")
