"""part_plate.py — Orchestrator Pad TOP PLATE (SPEC.md "Top plate").

One printable part, built as a union of individually-watertight shells
(no 3D CSG — the slicer unions overlapping shells):

  * plate slab in two Z bands (counterbore trick):
      band A  Z 28.0..28.7  — outline minus 14 MX cutouts, knob hole,
                              4x Ø3.4 screw through-holes
      band B  Z 28.5..29.5  — same, but corner holes are Ø6.4 counterbores
    the 0.2 overlap fuses the bands; net effect: full 1.5 plate with an
    0.8-deep Ø6.4 counterbore over a Ø3.4 through-hole at each corner.
  * skirt (drops into the tray's thinned upper wall), Z 21.5..28.2 — the ring
    is notched so the case can close and USB can mate:
      - Ø8.6 corner clearances at (±39, ±39) around the tray bosses (Ø7.0
        rises to Z 25.5, straight through the skirt band; 0.8 radial gap)
      - ONE back notch x -14..+14 (full skirt depth): the tray's USB window
        (26 wide, Z 17.0..23.5) crosses the 21.5 ledge, so its upper band
        runs through the skirt seat — the notch opens the whole corridor
        for the window and the plug hood
    the remaining segments each still fuse to plate band A via the 0.2 lap.
    (v3's separate USB/UART and front mic notches are gone: the v4 mic
    grille sits at Z 19.4..20.9, fully below the ledge.)
  * 4 screw towers Ø7.6/Ø3.4 at (±39, ±39), Z 25.5..28.2
    (towers land on the tray bosses; 0.2 into the plate slab)

World position per SPEC: XY centered on the case footprint, Z as listed.
"""
from __future__ import annotations

import os
import sys

from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union

import partlib as pl
import part_tray                    # single source of truth for the USB slot X

# ---- local parameters (SPEC "Top plate" / kernel overlap rule) ------------

OVERLAP = 0.2                       # min Z overlap so shells fuse when sliced
MX_CORNER_R = 0.5                   # MX cutout corner radius
SCREW_D = 3.4                       # M3 through-hole
CBORE_D = 6.4                       # M3 button-head counterbore
CBORE_DEPTH = 0.8                   # counterbore depth from the top face
SKIRT_OUT_W, SKIRT_OUT_R = 87.3, 6.9    # skirt outer profile (rr) — 0.15 per
                                    # side inside the tray's 87.6 upper wall
SKIRT_IN_W, SKIRT_IN_R = 85.0, 6.3      # skirt inner profile (1.15 wall)
BOSS_CLEAR_D = 8.6                  # skirt corner notch around the Ø7.0 tray
                                    # bosses (0.8 radial clearance)
USB_NOTCH_X0, USB_NOTCH_X1 = -14.0, 14.0    # back notch: the tray's 26-wide
                                    # USB window (Z 17.0..23.5) crosses the
                                    # 21.5 ledge into the skirt band
USB_NOTCH_Y0, USB_NOTCH_Y1 = 41.0, 44.0     # full skirt band (y 42.5..43.65)
TOWER_D = 7.6                       # screw tower outer diameter
TOWER_Z0 = part_tray.BOSS_TOP       # tray corner-boss top (25.5, SPEC "Tray")

# ---- v5 switch sockets (donor-keyboard style, SPEC "Top plate") -----------
# Each switch drops into a pocket under its plate cutout and its BASE seats
# on a socket floor at exactly plate_top - 5.0 (the MX under-shoulder depth),
# so the clips engage the 1.5 plate as usual while the body is fully caged.
# The floor carries the MX footprint holes; the two contact pins protrude
# ~2.1 below it — a solder-ready back face, like a PCB.
SOCKET_WALL = 1.6                   # pocket wall thickness
SOCKET_OUT_W = 17.3                 # pocket outer square (14.1 + 2*1.6)
SOCKET_OUT_R = 1.7
SOCKET_SEAT_DROP = 5.0              # MX shoulder->base depth below plate top
SOCKET_FLOOR_T = 1.2
MX_POST_D = 4.3                     # center post hole
MX_PIN_D = 2.8                      # the two contact pin holes
MX_PIN_A = (-3.81, 2.54)            # contact 1 (offsets from key center,
MX_PIN_B = (2.54, 5.08)             #  +Y toward the back — donor layout)
MX_LEG_D = 2.0                      # 5-pin plastic leg holes (compatibility)
MX_LEGS = ((-5.08, 0.0), (5.08, 0.0))
TOWER_CLEAR_D = 8.8                 # socket keep-out around the screw towers


def _at(geom, x, y):
    return affinity.translate(geom, x, y)


def _screw_centers():
    return [(sx * pl.BOSS_XY, sy * pl.BOSS_XY)
            for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]


def _plate_profile(corner_hole_d):
    """Plate outline minus MX cutouts, knob hole and 4 corner holes of the
    given diameter (Ø3.4 through-band / Ø6.4 counterbore band)."""
    outline = pl.rounded_rect(pl.CASE_W, pl.CASE_W, pl.CASE_R)
    cuts = [_at(pl.rounded_rect(pl.MX_CUT, pl.MX_CUT, MX_CORNER_R),
                k["x"], k["y"])
            for k in pl.key_layout()]                       # 14 MX cutouts
    cuts.append(_at(pl.circle(pl.KNOB_HOLE_D), *pl.KNOB_POS))  # EC11 bush
    cuts += [_at(pl.circle(corner_hole_d), x, y)
             for x, y in _screw_centers()]                  # corner holes
    return outline.difference(unary_union(cuts))


def _skirt_profile():
    """Skirt ring minus the tray-boss corner clearances and the back (USB
    window) notch.

    The Ø7.0 tray bosses rise to Z 25.5 straight through the skirt band
    (their reach past the shared corner-arc center exceeds even the skirt's
    outer radius), and the back band would stand over the USB window's
    upper band (the window top 23.5 crosses the 21.5 ledge) — the notches
    are mandatory for the case to close / the plug to mate. The cuts split
    the ring into segments; every segment still spans the full skirt
    height, so each stays a watertight prism fused to plate band A by the
    0.2 overlap.
    """
    skirt = pl.ring2d(pl.rounded_rect(SKIRT_OUT_W, SKIRT_OUT_W, SKIRT_OUT_R),
                      pl.rounded_rect(SKIRT_IN_W, SKIRT_IN_W, SKIRT_IN_R))
    boss_clear = unary_union([_at(pl.circle(BOSS_CLEAR_D), x, y)
                              for x, y in _screw_centers()])
    usb_notch = box(USB_NOTCH_X0, USB_NOTCH_Y0, USB_NOTCH_X1, USB_NOTCH_Y1)
    return skirt.difference(boss_clear).difference(usb_notch)


def _tower_keepout():
    return unary_union([_at(pl.circle(TOWER_CLEAR_D), x, y)
                        for x, y in _screw_centers()])


def _socket_shells(key, keepout):
    """Pocket wall ring + footprint floor for one switch, in world XY.
    Returns (wall_geom, floor_geom) 2D profiles (may be clipped by the
    screw-tower keep-out on the three corner-adjacent keys)."""
    x, y = key["x"], key["y"]
    outer = _at(pl.rounded_rect(SOCKET_OUT_W, SOCKET_OUT_W, SOCKET_OUT_R), x, y)
    inner = _at(pl.rounded_rect(pl.MX_CUT, pl.MX_CUT, MX_CORNER_R), x, y)
    wall = outer.difference(inner).difference(keepout)
    holes = [_at(pl.circle(MX_POST_D), x, y),
             _at(pl.circle(MX_PIN_D), x + MX_PIN_A[0], y + MX_PIN_A[1]),
             _at(pl.circle(MX_PIN_D), x + MX_PIN_B[0], y + MX_PIN_B[1])]
    holes += [_at(pl.circle(MX_LEG_D), x + lx, y + ly) for lx, ly in MX_LEGS]
    floor = outer.difference(unary_union(holes)).difference(keepout)
    return wall, floor


def build():
    z_a1 = pl.PLATE_Z1 - CBORE_DEPTH        # 28.7 — deep band top
    z_b0 = z_a1 - OVERLAP                   # 28.5 — counterbore band bottom
    z_into_plate = pl.PLATE_Z0 + OVERLAP    # 28.2 — skirt/tower fuse height
    seat_z = pl.PLATE_Z1 - SOCKET_SEAT_DROP  # 24.5 — switch base seat
    floor_z0 = seat_z - SOCKET_FLOOR_T       # 23.3 — socket floor bottom

    m = pl.Mesh()

    # plate slab, two bands (holes are through BOTH bands except the corner
    # holes, which widen from Ø3.4 to the Ø6.4 counterbore in the top band)
    m += pl.prism(_plate_profile(SCREW_D), pl.PLATE_Z0, z_a1)
    m += pl.prism(_plate_profile(CBORE_D), z_b0, pl.PLATE_Z1)

    # skirt: seats inside the tray's thinned upper wall (boss + USB notches)
    m += pl.prism(_skirt_profile(), pl.LEDGE_Z, z_into_plate)

    # 4 screw towers: continue the Ø3.4 bore down to the tray bosses
    for x, y in _screw_centers():
        tower = pl.ring2d(_at(pl.circle(TOWER_D), x, y),
                          _at(pl.circle(SCREW_D), x, y))
        m += pl.prism(tower, TOWER_Z0, z_into_plate)

    # v5: one socket box per switch — wall ring up into the plate, footprint
    # floor at the MX base seat (floor overlaps the wall ring radially over
    # floor_z0..seat_z, so the box fuses into one printable body)
    keepout = _tower_keepout()
    for key in pl.key_layout():
        wall, floor = _socket_shells(key, keepout)
        m += pl.prism(wall, floor_z0, z_into_plate)
        m += pl.prism(floor, floor_z0, seat_z)

    return [("plate", m, pl.COLORS["plate"])]


if __name__ == "__main__":
    items = build()
    all_ok = True
    for name, mesh, _color in items:
        rep = pl.validate(mesh)
        print(name, rep)
        all_ok &= rep["watertight"]

    here = os.path.dirname(os.path.abspath(__file__))
    exports = os.path.normpath(os.path.join(here, "..", "exports"))
    os.makedirs(exports, exist_ok=True)
    out = os.path.join(exports, "preview-plate.glb")
    pl.glb_write(out, items)
    print("wrote", out)
    sys.exit(0 if all_ok else 1)
