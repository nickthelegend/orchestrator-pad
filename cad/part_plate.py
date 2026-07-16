"""part_plate.py — Orchestrator Pad TOP PLATE (SPEC.md "Top plate").

One printable part, built as a union of individually-watertight shells
(no 3D CSG — the slicer unions overlapping shells):

  * plate slab in two Z bands (counterbore trick):
      band A  Z 17.5..18.2  — outline minus 14 MX cutouts, knob hole,
                              4x Ø3.4 screw through-holes
      band B  Z 18.0..19.0  — same, but corner holes are Ø6.4 counterbores
    the 0.2 overlap fuses the bands; net effect: full 1.5 plate with an
    0.8-deep Ø6.4 counterbore over a Ø3.4 through-hole at each corner.
  * skirt (drops into the tray's thinned upper wall), Z 11.0..17.7 — the ring
    is notched so the case can close and USB can mate:
      - Ø8.6 corner clearances at (±39, ±39) around the tray bosses (Ø7.0
        rises to Z 15.0, straight through the skirt band; 0.8 radial gap)
      - back notch x -13.3..+14.79 (full skirt depth): clears the native
        USB plug corridor, the UART shell and the UART relief pocket
      - front-center notch x -9..+9 (full skirt depth): room for the
        INMP441 mic breakout glued behind the mic holes
    the remaining segments each still fuse to plate band A via the 0.2 lap.
  * 4 screw towers Ø7.6/Ø3.4 at (±39, ±39), Z 15.0..17.7
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
USB_NOTCH_X0, USB_NOTCH_X1 = -13.3, 14.79   # back notch: covers the native
                                    # plug corridor + UART shell/relief pocket
USB_NOTCH_Y0, USB_NOTCH_Y1 = 41.0, 44.0     # full skirt band (y 42.5..43.65)
MIC_NOTCH_X = 9.0                   # front-center notch |x| <= 9.0 (INMP441
MIC_NOTCH_Y0, MIC_NOTCH_Y1 = -44.0, -41.0   # breakout behind the mic holes)
TOWER_D = 7.6                       # screw tower outer diameter
TOWER_Z0 = part_tray.BOSS_TOP       # tray corner-boss top (15.0, SPEC "Tray")


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
    """Skirt ring minus the tray-boss corner clearances, the back (USB/UART)
    notch and the front-center (mic breakout) notch.

    The Ø7.0 tray bosses rise to Z 15.0 straight through the skirt band
    (their reach past the shared corner-arc center exceeds even the skirt's
    outer radius), and the back band would stand over both USB-port
    corridors and the UART relief pocket — the notches are mandatory for
    the case to close / the plug to mate. The cuts split the ring into
    segments; every segment still spans the full skirt height, so each
    stays a watertight prism fused to plate band A by the 0.2 overlap.
    """
    skirt = pl.ring2d(pl.rounded_rect(SKIRT_OUT_W, SKIRT_OUT_W, SKIRT_OUT_R),
                      pl.rounded_rect(SKIRT_IN_W, SKIRT_IN_W, SKIRT_IN_R))
    boss_clear = unary_union([_at(pl.circle(BOSS_CLEAR_D), x, y)
                              for x, y in _screw_centers()])
    usb_notch = box(USB_NOTCH_X0, USB_NOTCH_Y0, USB_NOTCH_X1, USB_NOTCH_Y1)
    mic_notch = box(-MIC_NOTCH_X, MIC_NOTCH_Y0, MIC_NOTCH_X, MIC_NOTCH_Y1)
    return (skirt.difference(boss_clear).difference(usb_notch)
                 .difference(mic_notch))


def build():
    z_a1 = pl.PLATE_Z1 - CBORE_DEPTH        # 18.2 — deep band top
    z_b0 = z_a1 - OVERLAP                   # 18.0 — counterbore band bottom
    z_into_plate = pl.PLATE_Z0 + OVERLAP    # 17.7 — skirt/tower fuse height

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
