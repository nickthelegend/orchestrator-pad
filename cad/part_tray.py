"""part_tray.py — Orchestrator Pad bottom shell (tray), in world position per SPEC.

One printable part = a union of individually-watertight prism shells that
overlap by OVL = 0.2 mm in Z wherever they stack (the slicer fuses them):

  floor   two slabs; the lower one carries the 4 feet-recess holes.
  walls   TWO concentric columns, each split into Z bands (band-split trick)
          so the USB-C slot, the UART relief pocket and the mic ports keep
          their exact spec edges: a band that carries a wall opening is
          stretched 0.2 into its solid neighbours (its cut runs the band's
          full height) while the solid neighbour ends exactly at the opening
          edge — the neighbour's cap face IS the opening's top/bottom face.
            outer column: the 1.2 skirt-seat wall profile, floor to TRAY_H
            liner column: the inner 1.2 (thick-wall remainder), floor to the
            ledge at Z=11.0; laps 0.2 radially into the outer column so the
            two columns fuse. Its top cap IS the ledge face. (Over the
            USB/UART corridors the liner's opening ceilings coincide with
            the ledge plane — 0.1 above the 10.9 spec edge, hidden inside
            the skirt-notch corridor; the outer skin keeps the exact 10.9.)
  rib     forward Y-stop for the board (USB insertion force).
  bosses  4 corner screw bosses: solid base + insert-bore ring.
  rails   2 ridges guiding the ESP32-S3 DevKitC laterally (USB end toward +Y).
  pads    2 pedestals under the board's bare center strip seating the PCB
          bottom at Z=5.4 (rail-top height) so the USB port faces the slot.
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

USB_W = 10.5                               # USB-C slot, back wall (Y=+45)
USB_X = 7.79                               # slot center X: the DevKitC-1 V1.1
#            drawing puts BOTH USB ports +-7.79 off the board centerline, so a
#            centered slot faces neither port. With the board centered by the
#            rails, the native/OTG port (HID + power + flashing) lands at
#            world X = +7.79 — the slot is centered on it.
USB_Z0, USB_Z1 = 6.4, 10.9                 # slot spans Z 6.4..10.9 (4.5 tall)

UART_X0, UART_X1 = -13.3, -2.3             # UART-port relief pocket, back wall:
UART_SKIN_Y = 44.1                         # inner-face rebate x -13.3..-2.3,
#            Z 6.4..10.9, floor at y=+44.1 (0.9 outer skin). The second (UART)
#            USB shell spans x -12.26..-3.32 and overhangs the board edge
#            ~1.31 — without the pocket it props the board off the back wall
#            and the native port can never reach its slot.

MIC_W = 1.5                                # three square mic ports, front wall
MIC_XS = (-3.0, 0.0, 3.0)
PORT_Z0, PORT_Z1 = 7.25, 8.75              # mic ports: centered Z=8

RIB_HALF_W = 9.0                           # forward Y-stop rib: |x| <= 9.0,
RIB_Y0, RIB_Y1 = -21.7, -20.6              # 1.1 thick, 0.33 ahead of the board
RIB_TOP = 6.9                              # front edge; top clears the antenna
#            overhang (Z 7.0) by 0.1 — the board cannot slide forward under
#            USB insertion force (5-20 N).

BOSS_D = 7.0                               # corner boss outer diameter
BORE_D = 4.0                               # M3 heat-set insert bore
BOSS_SOLID_TOP = 9.0                       # solid pedestal 2.2..9.0
BOSS_TOP = 15.0                            # bore ring 8.8..15.0 (bore 6.0 deep)

RAIL_W = 2.0                               # ESP32 rails: 2 wide x 3 tall x 40
RAIL_GAP = 26.0                            # inner faces 26.0 apart
RAIL_Y0, RAIL_Y1 = -2.0, 38.0              # along Y, USB end toward back wall
RAIL_TOP = pl.FLOOR + 3.0                  # 5.4

# Board support pads: the 25.4-wide board drops BETWEEN the 26.0-gap rails, so
# the rails are lateral guides only — these pads carry the PCB bottom at the
# rail-top height Z=5.4 (USB centerline then 5.4 + 1.6 + 1.63 = 8.63, centered
# in the 6.4..10.9 slot). They sit under the board's bare center strip,
# |x| <= 9.0, clear of the header rows (insulators cover |x| >= 10.16) and of
# the connector underside tabs near the back edge. BOM: header-less or
# clipped-flush pins — the 2.4 floor can never clear 8.5 mm factory pins.
PAD_HALF_W = 9.0                           # pads span x -9.0..+9.0
PAD_TOP = RAIL_TOP                         # PCB bottom seats at 5.4
PAD_YS = ((2.0, 8.0), (24.0, 30.0))        # two pads along the rail span

# reach of the wall-opening cutters: from inside any wall to past the outside
CUT_IN, CUT_OUT = HALF - 4.0, HALF + 1.0   # 41 .. 46


def _rr(w, r):
    """Square rounded-rect profile centered at origin."""
    return pl.rounded_rect(w, w, r)


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

    # wall-opening cutters (2D). usb reaches fully through the wall; the
    # UART pocket cutter stops at the pocket floor y=44.1 (0.9 outer skin):
    # wall material x -13.3..-2.3 exists only for y > 44.1 in the cut bands.
    usb = box(USB_X - USB_W / 2, CUT_IN, USB_X + USB_W / 2, CUT_OUT)
    uart = box(UART_X0, CUT_IN, UART_X1, UART_SKIN_Y)
    back = usb.union(uart)                 # both share Z 6.4..10.9
    mics = unary_union([box(x - MIC_W / 2, -CUT_OUT, x + MIC_W / 2, -CUT_IN)
                        for x in MIC_XS])  # mic ports: Z 7.25..8.75

    m = pl.Mesh()

    # -- floor: recess layer (holes through it) + full slab above ----------
    # The hole layer runs 0.2 past the recess depth; the full slab starts at
    # the exact recess depth, so its bottom cap is the recess ceiling at 0.6.
    feet = unary_union([affinity.translate(pl.circle(FEET_D),
                                           sx * FEET_XY, sy * FEET_XY)
                        for sx in (-1, 1) for sy in (-1, 1)])
    m += pl.prism(outer.difference(feet), 0.0, FEET_DEPTH + OVL)
    m += pl.prism(outer, FEET_DEPTH, pl.FLOOR)

    # -- walls: two columns of Z bands; cut bands stretch OVL into solid
    #    neighbours, solid neighbours' caps define the exact opening edges --
    for ring, top in ((ring_thin, pl.TRAY_H), (ring_liner, pl.LEDGE_Z)):
        # 2.2..6.4    solid (top cap = USB slot / UART pocket floor at 6.4)
        m += pl.prism(ring, pl.FLOOR - OVL, USB_Z0)
        # 6.2..7.25   - USB - UART   (top cap = mic port floor at 7.25)
        m += pl.prism(ring.difference(back), USB_Z0 - OVL, PORT_Z0)
        # 7.05..8.95  - USB - UART - mics   (stretched both ways; the mic
        #             edges at 7.25/8.75 come from the solid caps around it)
        m += pl.prism(ring.difference(back).difference(mics),
                      PORT_Z0 - OVL, PORT_Z1 + OVL)
        if ring is ring_thin:
            # 8.75..11.1  - USB - UART  (bottom cap = mic ceiling at 8.75)
            m += pl.prism(ring.difference(back), PORT_Z1, USB_Z1 + OVL)
            # 10.9..17.5  solid (bottom cap = USB/UART ceiling at 10.9)
            m += pl.prism(ring, USB_Z1, pl.TRAY_H)
        else:
            # 8.75..11.0  - USB - UART: bottom cap = mic ceiling at 8.75,
            #             top cap = the skirt-seat LEDGE face at 11.0
            m += pl.prism(ring.difference(back), PORT_Z1, top)

    # -- forward Y-stop rib (board slides no further than the rib face) ----
    m += pl.prism(box(-RIB_HALF_W, RIB_Y0, RIB_HALF_W, RIB_Y1),
                  pl.FLOOR - OVL, RIB_TOP)

    # -- corner bosses: solid pedestal + insert-bore ring ------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * pl.BOSS_XY, sy * pl.BOSS_XY
            c_boss = affinity.translate(pl.circle(BOSS_D), cx, cy)
            c_bore = affinity.translate(pl.circle(BORE_D), cx, cy)
            m += pl.prism(c_boss, pl.FLOOR - OVL, BOSS_SOLID_TOP)
            m += pl.prism(c_boss.difference(c_bore),
                          BOSS_SOLID_TOP - OVL, BOSS_TOP)

    # -- ESP32-S3 DevKitC locating rails (lateral guides) ------------------
    for s in (-1, 1):
        x_in, x_out = s * (RAIL_GAP / 2), s * (RAIL_GAP / 2 + RAIL_W)
        m += pl.prism(box(min(x_in, x_out), RAIL_Y0, max(x_in, x_out), RAIL_Y1),
                      pl.FLOOR - OVL, RAIL_TOP)

    # -- board support pads: PCB bottom seats at Z 5.4 ---------------------
    for y0, y1 in PAD_YS:
        m += pl.prism(box(-PAD_HALF_W, y0, PAD_HALF_W, y1),
                      pl.FLOOR - OVL, PAD_TOP)

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
