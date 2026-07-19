"""part_tray.py — Orchestrator Pad bottom shell (tray, v4 "fat base"), in
world position per SPEC.

The interior is a component bay: the dual-USB-C ESP32-S3 clone board rides
high (underside at Z=16.0, factory header pins DOWN into the bay), a
down-firing cavity speaker sits flange-on-floor under the board's front
half, the MAX98357A amp drops into a ridge-framed pocket, and jumper-wire
bundles tie to notched posts along the west wall.

One printable part = a union of individually-watertight prism shells that
overlap by OVL = 0.2 mm in Z (or radially) wherever they stack (the slicer
fuses them):

  floor    two slabs; the lower one carries the 4 feet-recess holes; BOTH
           carry the speaker grille slots and the 4 M2.5 pilot holes.
  walls    TWO concentric columns, each split into Z bands (band-split
           trick) so the USB window and the mic ports keep their exact spec
           edges: a band that carries a wall opening is stretched 0.2 into
           its solid neighbours (its cut runs the band's full height) while
           the solid neighbour ends exactly at the opening edge — the
           neighbour's cap face IS the opening's top/bottom face.
             outer column: the 1.2 skirt-seat wall profile, floor to TRAY_H
             liner column: the inner 1.2 (thick-wall remainder), floor to
             the ledge at Z=21.5; laps 0.2 radially into the outer column
             so the two columns fuse. Its top cap IS the ledge face. (The
             USB window 17.0..23.5 crosses the ledge: through the liner the
             opening ceiling coincides with the ledge plane; the outer skin
             keeps the exact 17.0/23.5 edges. The plate skirt is notched
             over the window's upper band.)
  bosses   4 corner screw bosses: solid pedestal + insert-bore ring.
  shelf    back board shelf (tab off the back wall): board back edge seats
           on its Z=16.0 top face.
  bridge   front bridge wall from the floor to Z=16.0: mid-span support
           between the speaker bay and the wiring bay.
  posts    4 Ø5 locator posts caging the board laterally (tops Z 19.0).
  amp      four L-corner ridges framing the MAX98357A pocket (foam-tape).
  wire     two Ø5 zip-tie posts with through-notches (band-split in Z).
"""
from __future__ import annotations

import os
import sys

from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union

import partlib as pl

OVL = 0.2                                  # standard Z overlap between shells

# ---------------------------------------------------------- tray numbers ----
HALF = pl.CASE_W / 2.0                     # 45.0 — outer face of the walls

SKIRT_WALL = 1.2                           # wall thickness above LEDGE_Z (spec)

FEET_XY = 36.0                             # feet-recess centers (+-36, +-36)
FEET_D = 9.0                               # recess diameter
FEET_DEPTH = 0.6                           # recess depth into the bottom face

# USB window, back wall (Y=+45): both board-top USB-C ports exit here. Wide
# and tall enough that the exact port offsets of any clone don't matter and
# a plug hood fits inside the aperture (supersedes the v3 X=+7.79 slot and
# the UART relief pocket).
WIN_W, WIN_Z0, WIN_Z1 = pl.USB_WIN         # 26.0 wide, centered X=0, Z 17.0..23.5

# Mic grille, front wall (Y=-45): 3 square ports, fully below the ledge.
# The round I2S mic module glues behind them, above the speaker body
# (supersedes the v3 low-Z round ports).
MIC_W = 1.5                                # port width/height (square)
MIC_XS = (-23.0, -20.0, -17.0)             # spacing 3.0, centered X=-20
MIC_Z0, MIC_Z1 = 19.4, 20.9                # 1.5 tall, ceiling 0.6 under LEDGE_Z

BOSS_D = 7.0                               # corner boss outer diameter
BORE_D = 4.0                               # M3 heat-set insert bore
BOSS_SOLID_TOP = 19.5                      # solid pedestal 2.2..19.5 (bore floor)
BOSS_TOP = 25.5                            # bore ring 19.3..25.5 (bore 6.0 deep)

# Board bay: board components-UP, header pins DOWN, centered X=0, back edge
# at Y=+42.0, up to BOARD_W x BOARD_L (30 x 64). Underside seats at BOARD_Z
# = 16.0 on the back shelf + front bridge; the locator posts cage it
# laterally (0.1 clearance per side to a 30-wide board). Under-board
# clearance floor->16.0 = 13.6 for the factory header pins + angled dupont
# connectors.
SHELF_X = 14.0                             # back shelf |x| <= 14
SHELF_Y0 = HALF - pl.WALL - 1.6            # 41.0 — tab protrudes 1.6 from the
SHELF_Y1 = HALF - pl.WALL + OVL            # 42.8 —  wall inner face (0.2 lap)
SHELF_Z0 = 13.5                            # shelf body 13.5..16.0

BRIDGE_X = 16.0                            # front bridge wall |x| <= 16
BRIDGE_Y0, BRIDGE_Y1 = 4.0, 7.0            # 3.0 thick, floor..16.0

POST_D = 5.0                               # Ø5 locator posts, tops Z 19.0
POST_TOP = 19.0
POST_XY = ((-17.6, 40.0), (17.6, 40.0), (-17.6, 5.5), (17.6, 5.5))

# Speaker bay (down-firing, flange ON the floor, centered SPK_CENTER):
# racetrack floor opening with two grille bars -> 3 slots; 4 M2.5
# self-tapper pilots THROUGH the floor (heads inside on the flange, tips
# end in the >=3mm foot gap). Fits flanges up to SPK_FLANGE (72x42), driver
# bump up to Ø50 x SPK_BUMP_MAX (11) tall: bump top 2.4+1.5+11 = 14.9
# clears the board underside at 16.0 by 1.1.
SPK_OPEN_W, SPK_OPEN_H = 54.0, 24.0        # racetrack opening (rounded R12)
SPK_OPEN_R = 12.0
SPK_BAR_W = 2.0                            # two bars along X -> 3 slots
SPK_PILOT_D = 2.4                          # M2.5 pilot holes, through the floor
SPK_PILOT_XY = tuple((sx * 31.5, y)        # 63 x 33 hole pattern @ (0,-21)
                     for sx in (-1, 1) for y in (-37.5, -4.5))

# Amp pocket: four L-corner ridges framing a square pocket east of the
# board — the MAX98357A drops in, foam-tape mounted.
AMP_C = (31.0, 14.0)                       # pocket center
AMP_POCKET = 20.0                          # pocket clear width (square)
AMP_RIDGE_W = 1.5                          # ridge width
AMP_RIDGE_H = 2.0                          # ridge height above the floor
AMP_RIDGE_L = 6.0                          # leg length from each outer corner

# Wire posts (west wiring channel): Ø5 x 8.0 tall, each with a zip-tie
# through-notch (open along X so a tie wraps a bundle running along Y).
WPOST_D = 5.0
WPOST_H = 8.0                              # above the floor top -> Z 10.4
WPOST_XY = ((-34.0, 12.0), (-34.0, 30.0))
NOTCH_W = 3.2                              # notch width (Y) for the tie
NOTCH_Z0, NOTCH_Z1 = 3.0, 5.0              # notch band (2.0 tall)

# reach of the wall-opening cutters: from inside any wall to past the outside
CUT_IN, CUT_OUT = HALF - 4.0, HALF + 1.0   # 41 .. 46


def _rr(w, r):
    """Square rounded-rect profile centered at origin."""
    return pl.rounded_rect(w, w, r)


def spk_floor_opening():
    """Speaker grille: racetrack 54 x 24 R12 at SPK_CENTER minus two 2.0
    bars along X -> a MultiPolygon of 3 slots (the actual floor holes)."""
    cx, cy = pl.SPK_CENTER
    track = affinity.translate(
        pl.rounded_rect(SPK_OPEN_W, SPK_OPEN_H, SPK_OPEN_R), cx, cy)
    slot_h = (SPK_OPEN_H - 2 * SPK_BAR_W) / 3.0          # 3 equal slots
    y0 = cy - SPK_OPEN_H / 2
    bars = unary_union([
        box(cx - SPK_OPEN_W / 2 - 1, y0 + slot_h, cx + SPK_OPEN_W / 2 + 1,
            y0 + slot_h + SPK_BAR_W),
        box(cx - SPK_OPEN_W / 2 - 1, y0 + 2 * slot_h + SPK_BAR_W,
            cx + SPK_OPEN_W / 2 + 1, y0 + 2 * (slot_h + SPK_BAR_W)),
    ])
    return track.difference(bars)


def amp_ridges():
    """Four L-corner ridges hugging the AMP_POCKET square from outside."""
    cx, cy = AMP_C
    h = AMP_POCKET / 2.0
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x_in, x_out = cx + sx * h, cx + sx * (h + AMP_RIDGE_W)
            y_in, y_out = cy + sy * h, cy + sy * (h + AMP_RIDGE_W)
            legs.append(box(min(x_in, x_out), min(y_out, y_out - sy * AMP_RIDGE_L),
                            max(x_in, x_out), max(y_out, y_out - sy * AMP_RIDGE_L)))
            legs.append(box(min(x_out, x_out - sx * AMP_RIDGE_L), min(y_in, y_out),
                            max(x_out, x_out - sx * AMP_RIDGE_L), max(y_in, y_out)))
    return unary_union(legs)


def build():
    """-> [("tray", Mesh, COLORS["tray"])] in world position (Z=0 = bottom)."""
    outer = _rr(pl.CASE_W, pl.CASE_R)
    # outer column: the 1.2 skirt-seat wall, full height (43.8..45.0 radial)
    ring_thin = pl.ring2d(outer, _rr(pl.CASE_W - 2 * SKIRT_WALL,
                                     pl.CASE_R - SKIRT_WALL))
    # liner column: the inner 1.2 of the 2.4 wall, floor..LEDGE_Z; its outer
    # boundary laps 0.2 into the outer column so the two columns fuse
    # (concentric corner arcs — every profile shares corner centers)
    ring_liner = pl.ring2d(_rr(pl.CASE_W - 2 * SKIRT_WALL + 2 * OVL,
                               pl.CASE_R - SKIRT_WALL + OVL),
                           _rr(pl.CASE_W - 2 * pl.WALL, pl.CASE_R - pl.WALL))

    # wall-opening cutters (2D), reaching fully through both columns
    win = box(-WIN_W / 2, CUT_IN, WIN_W / 2, CUT_OUT)         # Z 17.0..23.5
    mics = unary_union([box(x - MIC_W / 2, -CUT_OUT, x + MIC_W / 2, -CUT_IN)
                        for x in MIC_XS])                     # Z 19.4..20.9

    m = pl.Mesh()

    # -- floor: recess layer (holes through it) + full slab above ----------
    # The hole layer runs 0.2 past the recess depth; the full slab starts at
    # the exact recess depth, so its bottom cap is the recess ceiling at 0.6.
    # The speaker slots + M2.5 pilots go through BOTH layers. (The two back
    # pilots merge with the adjacent feet-recess rims in the lower layer —
    # a designed 63x33 speaker pattern vs (+-36,+-36) feet consequence; the
    # merged 2D holes keep both layers watertight.)
    feet = unary_union([affinity.translate(pl.circle(FEET_D),
                                           sx * FEET_XY, sy * FEET_XY)
                        for sx in (-1, 1) for sy in (-1, 1)])
    slots = spk_floor_opening()
    pilots = unary_union([affinity.translate(pl.circle(SPK_PILOT_D), x, y)
                          for x, y in SPK_PILOT_XY])
    thru = slots.union(pilots)
    m += pl.prism(outer.difference(feet.union(thru)), 0.0, FEET_DEPTH + OVL)
    m += pl.prism(outer.difference(thru), FEET_DEPTH, pl.FLOOR)

    # -- walls: two columns of Z bands; cut bands stretch OVL into solid
    #    neighbours, solid neighbours' caps define the exact opening edges --
    for ring, top in ((ring_thin, pl.TRAY_H), (ring_liner, pl.LEDGE_Z)):
        # 2.2..17.0   solid (top cap = USB window floor at 17.0)
        m += pl.prism(ring, pl.FLOOR - OVL, WIN_Z0)
        # 16.8..19.4  - window   (top cap = mic port floor at 19.4)
        m += pl.prism(ring.difference(win), WIN_Z0 - OVL, MIC_Z0)
        # 19.2..21.1  - window - mics   (stretched both ways; the mic edges
        #             at 19.4/20.9 come from the solid caps around it)
        m += pl.prism(ring.difference(win).difference(mics),
                      MIC_Z0 - OVL, MIC_Z1 + OVL)
        if ring is ring_thin:
            # 20.9..23.7  - window  (bottom cap = mic ceiling at 20.9)
            m += pl.prism(ring.difference(win), MIC_Z1, WIN_Z1 + OVL)
            # 23.5..28.0  solid (bottom cap = window ceiling at 23.5)
            m += pl.prism(ring, WIN_Z1, pl.TRAY_H)
        else:
            # 20.9..21.5  - window: bottom cap = mic ceiling at 20.9, top
            #             cap = the skirt-seat LEDGE face at 21.5 (the
            #             window's liner ceiling IS the ledge plane)
            m += pl.prism(ring.difference(win), MIC_Z1, top)

    # -- corner bosses: solid pedestal + insert-bore ring ------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * pl.BOSS_XY, sy * pl.BOSS_XY
            c_boss = affinity.translate(pl.circle(BOSS_D), cx, cy)
            c_bore = affinity.translate(pl.circle(BORE_D), cx, cy)
            m += pl.prism(c_boss, pl.FLOOR - OVL, BOSS_SOLID_TOP)
            m += pl.prism(c_boss.difference(c_bore),
                          BOSS_SOLID_TOP - OVL, BOSS_TOP)

    # -- board bay: back shelf (tab off the wall, 0.2 radial lap into the
    #    liner), front bridge wall, 4 locator posts ------------------------
    m += pl.prism(box(-SHELF_X, SHELF_Y0, SHELF_X, SHELF_Y1),
                  SHELF_Z0, pl.BOARD_Z)
    m += pl.prism(box(-BRIDGE_X, BRIDGE_Y0, BRIDGE_X, BRIDGE_Y1),
                  pl.FLOOR - OVL, pl.BOARD_Z)
    for x, y in POST_XY:
        m += pl.prism(affinity.translate(pl.circle(POST_D), x, y),
                      pl.FLOOR - OVL, POST_TOP)

    # -- amp pocket ridges (MAX98357A drops between them) ------------------
    m += pl.prism(amp_ridges(), pl.FLOOR - OVL, pl.FLOOR + AMP_RIDGE_H)

    # -- wire posts with zip-tie through-notches (band-split in Z) ---------
    for x, y in WPOST_XY:
        c = affinity.translate(pl.circle(WPOST_D), x, y)
        notch = box(x - WPOST_D, y - NOTCH_W / 2, x + WPOST_D, y + NOTCH_W / 2)
        # 2.2..3.0  solid (top cap = notch floor at 3.0)
        m += pl.prism(c, pl.FLOOR - OVL, NOTCH_Z0)
        # 2.8..5.2  - notch (two side slivers; exact edges from the caps)
        m += pl.prism(c.difference(notch), NOTCH_Z0 - OVL, NOTCH_Z1 + OVL)
        # 5.0..10.4 solid (bottom cap = notch ceiling at 5.0)
        m += pl.prism(c, NOTCH_Z1, pl.FLOOR + WPOST_H)

    return [("tray", m, pl.COLORS["tray"])]


if __name__ == "__main__":
    items = build()
    ok = True
    for name, mesh, _ in items:
        rep = pl.validate(mesh)
        print(f"{name}: {rep}")
        ok &= rep["watertight"]

    here = os.path.dirname(os.path.abspath(__file__))
    exports = os.path.normpath(os.path.join(here, "..", "exports"))
    os.makedirs(exports, exist_ok=True)
    out = os.path.join(exports, "preview-tray.glb")
    pl.glb_write(out, items)
    print("wrote", out)
    sys.exit(0 if ok else 1)
