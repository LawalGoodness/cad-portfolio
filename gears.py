"""Involute spur gear tooth profile generation.

Gear teeth are not arcs. The working flank of a spur gear tooth is an
*involute* of a base circle -- the curve traced by the end of a taut string
unwound from that circle -- and it is used because it is the only profile that
transmits constant angular velocity ratio regardless of small errors in centre
distance. Approximating the flank with an arc gives a gear that runs, but with
velocity ripple and a contact ratio you cannot calculate.

Everything below is generated from the standard involute relations rather than
imported from a gear library, because the point of the exercise is the
geometry.

Nomenclature (ISO 53 / standard spur gear practice), all lengths in mm:

    m       module, the size unit. pitch diameter = m * z
    z       number of teeth
    alpha   pressure angle, 20 degrees is the modern standard
    r_p     pitch radius     = m*z/2
    r_b     base radius      = r_p * cos(alpha)
    r_a     tip radius       = r_p + m          (external)
    r_f     root radius      = r_p - 1.25*m     (external)

For an internal (ring) gear the material is on the outside, so tip and root
swap sense: the tip radius is r_p - m and the root radius is r_p + 1.25*m.
"""

from __future__ import annotations

import math

PRESSURE_ANGLE = math.radians(20.0)
ADDENDUM_FACTOR = 1.00
DEDENDUM_FACTOR = 1.25


def involute(alpha: float) -> float:
    """The involute function, inv(a) = tan(a) - a."""
    return math.tan(alpha) - alpha


def _pressure_angle_at(r: float, r_b: float) -> float:
    """Pressure angle where the involute of base radius r_b crosses radius r."""
    ratio = r_b / r
    # Clamp: r below the base circle has no involute, and floating point can
    # push ratio a hair over 1 exactly at r == r_b.
    return math.acos(max(-1.0, min(1.0, ratio)))


def half_tooth_angle(
    r: float, r_b: float, z: int, backlash_angle: float, internal: bool
) -> float:
    """Angular half-thickness of the tooth at radius r.

    At the pitch circle a standard tooth occupies half the circular pitch, so
    its half-angle there is pi/(2z). Moving away from the pitch circle the
    flank follows the involute, and the correction is the difference of
    involute functions. For an internal gear the material lies on the far side
    of the flank, so that correction changes sign -- which is why the tooth of
    a ring gear grows wider as you move outward, while an external tooth grows
    narrower.
    """
    inv_r = involute(_pressure_angle_at(r, r_b))
    inv_pitch = involute(PRESSURE_ANGLE)
    if internal:
        phi = math.pi / (2 * z) - inv_pitch + inv_r
    else:
        phi = math.pi / (2 * z) + inv_pitch - inv_r
    return phi - backlash_angle


def _arc(r: float, a0: float, a1: float, steps: int) -> list[tuple[float, float]]:
    return [
        (r * math.cos(a0 + (a1 - a0) * i / steps), r * math.sin(a0 + (a1 - a0) * i / steps))
        for i in range(steps + 1)
    ]


def gear_profile(
    z: int,
    module: float,
    *,
    internal: bool = False,
    backlash: float = 0.05,
    flank_steps: int = 14,
    tip_steps: int = 3,
    root_steps: int = 4,
    phase: float = 0.0,
) -> list[tuple[float, float]]:
    """Closed anticlockwise outline of a spur gear, as 2D points.

    For an external gear this is the whole outline. For an internal gear it is
    the toothed bore, which the caller subtracts from an annulus.

    `backlash` is the circumferential tooth thinning at the pitch circle, in
    mm. Real gear trains need it for lubricant and thermal growth; here it also
    guarantees that meshing bodies have a measurable clearance, so an
    interference check has something unambiguous to assert.
    """
    r_p = module * z / 2
    r_b = r_p * math.cos(PRESSURE_ANGLE)
    if internal:
        r_tip = r_p - ADDENDUM_FACTOR * module
        r_root = r_p + DEDENDUM_FACTOR * module
    else:
        r_tip = r_p + ADDENDUM_FACTOR * module
        r_root = r_p - DEDENDUM_FACTOR * module

    backlash_angle = (backlash / 2) / r_p

    def phi(r: float) -> float:
        return half_tooth_angle(r, r_b, z, backlash_angle, internal)

    # The involute only exists at or outside the base circle. An external gear
    # cut with few teeth has its root below the base circle; that undercut
    # region is closed with a radial line, which is the usual simplification
    # when the trochoid produced by the real cutter is not being modelled.
    r_lo = max(r_root, r_b) if not internal else r_tip
    r_hi = r_tip if not internal else r_root

    flank = [r_lo + (r_hi - r_lo) * i / flank_steps for i in range(flank_steps + 1)]

    pts: list[tuple[float, float]] = []
    pitch = 2 * math.pi / z

    for k in range(z):
        beta = phase + k * pitch

        if internal:
            # Ring gear: tip is the innermost radius. Rising flank runs from
            # root (outer) inward to tip.
            a_start = beta - phi(r_root)
            pts.append((r_root * math.cos(a_start), r_root * math.sin(a_start)))
            for r in reversed(flank):
                a = beta - phi(r)
                pts.append((r * math.cos(a), r * math.sin(a)))
            pts += _arc(r_tip, beta - phi(r_tip), beta + phi(r_tip), tip_steps)[1:]
            for r in flank:
                a = beta + phi(r)
                pts.append((r * math.cos(a), r * math.sin(a)))
            a_end = beta + phi(r_root)
            nxt = phase + (k + 1) * pitch - phi(r_root)
            pts += _arc(r_root, a_end, nxt, root_steps)[1:-1]
        else:
            # External gear: radial line out of the root, up the flank, over
            # the tip, back down, radial line in, then the root arc.
            a_lo = beta - phi(r_lo)
            if r_root < r_lo:
                pts.append((r_root * math.cos(a_lo), r_root * math.sin(a_lo)))
            for r in flank:
                a = beta - phi(r)
                pts.append((r * math.cos(a), r * math.sin(a)))
            pts += _arc(r_tip, beta - phi(r_tip), beta + phi(r_tip), tip_steps)[1:]
            for r in reversed(flank):
                a = beta + phi(r)
                pts.append((r * math.cos(a), r * math.sin(a)))
            a_hi = beta + phi(r_lo)
            if r_root < r_lo:
                pts.append((r_root * math.cos(a_hi), r_root * math.sin(a_hi)))
            nxt = phase + (k + 1) * pitch - phi(r_lo)
            pts += _arc(r_root, a_hi, nxt, root_steps)[1:-1]

    return _dedupe(pts)


def _dedupe(pts: list[tuple[float, float]], tol: float = 1e-7):
    """Drop consecutive coincident points, including across the closure.

    Flank, tip arc and root arc segments each end where the next begins, so
    the naive concatenation repeats points at every junction. A repeated point
    is a zero-length edge, and OCCT refuses to build one -- the failure
    surfaces as StdFail_NotDone from make_line, which says nothing about the
    real cause. Cleaning the point list here is cheaper and far more robust
    than trimming each junction by hand.
    """
    out: list[tuple[float, float]] = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > tol:
            out.append(p)
    while len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= tol:
        out.pop()
    return out


def geometry(z: int, module: float, internal: bool = False) -> dict[str, float]:
    """The derived radii, for drawings and acceptance checks."""
    r_p = module * z / 2
    return {
        "pitch_r": r_p,
        "base_r": r_p * math.cos(PRESSURE_ANGLE),
        "tip_r": r_p - module if internal else r_p + module,
        "root_r": r_p + 1.25 * module if internal else r_p - 1.25 * module,
    }
