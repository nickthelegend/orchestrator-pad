"""audit_post_can.py — post-raise probe (read-only): module-can vs switch
underside, UART relief, Y-stop rib, and the fix-pass ACCEPTANCE TABLE.

Adapted from the RE-AUDIT 3 probe; expectations updated for the +3.5 case
raise (tray 17.5 / plate 17.5..19.0 / ledge 11.0) plus the UART relief
pocket, the forward Y-stop rib, the widened skirt (87.3) and its notches,
and the knob nut recess. Exits non-zero unless every check passes.

Component data (official V1.1 drawing / Cherry MX datasheet, as used by
audit_fit/audit_recheck):
  PCB 25.4 x 62.87 x 1.6, on pads -> bottom Z 5.4, top Z 7.0
  USB shells 8.94 w x 3.26 h at x = +-7.79, overhang the board edge 1.31
  WROOM-1 module 18.0 wide x 25.5 long x 3.1 tall, centered x=0, at the front
    end; antenna (~6.3 of the 25.5) overhangs the front edge (photos/V1.1);
    shield-can region on-board, top Z 10.1; antenna PCB ~1.0 thick, top ~8.0
  MX: plate top->housing base 5.0 -> base Z 14.0; center post + pins 3.3
    below base -> tips Z 10.7; post d4 at key center;
    pins (-3.81,+2.54),(+2.54,+5.08)
  EC11: M7 panel nut ~11.5 across corners, ~2.2 tall, sits on the plate top.
"""
import sys

import numpy as np
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union

import partlib as pl
import part_tray as pt
import part_plate as pp
import part_knob as pk
import part_caps as pc

BRD_W, BRD_L, BRD_T = 25.4, 62.87, 1.6
OVH = 1.31
SHELL_W = 8.94
PIN_TIP = pl.PLATE_Z1 - 8.3            # 10.7
HOUS_BOT = pl.PLATE_Z1 - 5.0           # 14.0
CAN_TOP = pt.PAD_TOP + BRD_T + 3.1     # 10.1
ANT_TOP = pt.PAD_TOP + BRD_T + 1.0     # ~8.0 (module PCB only, no can)
NUT_AF, NUT_H = 11.5, 2.2              # EC11 M7 panel nut

FAILURES = []


def check(name, ok):
    FAILURES.extend([] if ok else [name])
    return "PASS" if ok else "FAIL"


# ------------------------------------------------------------ winding ray ----
def winding_inside(mesh, pts, eps=1e-9):
    """Generalized winding via +Z ray: bool array 'inside any positive
    shell' (robust to the intended overlapping-shell construction)."""
    V, F = mesh._np()
    tri = V[F]
    ax, ay, az = tri[:, 0, 0], tri[:, 0, 1], tri[:, 0, 2]
    bx, by, bz = tri[:, 1, 0], tri[:, 1, 1], tri[:, 1, 2]
    cx, cy, cz = tri[:, 2, 0], tri[:, 2, 1], tri[:, 2, 2]
    area2 = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
    keep = np.abs(area2) > 1e-12
    ax, ay, az = ax[keep], ay[keep], az[keep]
    bx, by, bz = bx[keep], by[keep], bz[keep]
    cx, cy, cz = cx[keep], cy[keep], cz[keep]
    area2 = area2[keep]
    sgn = np.sign(area2).astype(np.int64)
    txmin = np.minimum(np.minimum(ax, bx), cx)
    txmax = np.maximum(np.maximum(ax, bx), cx)
    tymin = np.minimum(np.minimum(ay, by), cy)
    tymax = np.maximum(np.maximum(ay, by), cy)

    pts = np.asarray(pts, float)
    W = np.zeros(len(pts), np.int64)
    CH = 512
    for i0 in range(0, len(pts), CH):
        P = pts[i0:i0 + CH]
        pxmin, pxmax = P[:, 0].min(), P[:, 0].max()
        pymin, pymax = P[:, 1].min(), P[:, 1].max()
        m = (txmax >= pxmin) & (txmin <= pxmax) & (tymax >= pymin) & (tymin <= pymax)
        if not m.any():
            continue
        A2, S = area2[m][None, :], sgn[m][None, :]
        Ax, Ay, Az = ax[m][None, :], ay[m][None, :], az[m][None, :]
        Bx, By, Bz = bx[m][None, :], by[m][None, :], bz[m][None, :]
        Cx, Cy, Cz = cx[m][None, :], cy[m][None, :], cz[m][None, :]
        px, py, pz = P[:, 0][:, None], P[:, 1][:, None], P[:, 2][:, None]
        e0 = (Bx - Ax) * (py - Ay) - (By - Ay) * (px - Ax)
        e1 = (Cx - Bx) * (py - By) - (Cy - By) * (px - Bx)
        e2 = (Ax - Cx) * (py - Cy) - (Ay - Cy) * (px - Cx)
        inside2d = ((np.sign(e0) == S) | (np.abs(e0) < eps)) & \
                   ((np.sign(e1) == S) | (np.abs(e1) < eps)) & \
                   ((np.sign(e2) == S) | (np.abs(e2) < eps))
        zs = (e1 * Az + e2 * Bz + e0 * Cz) / A2
        crossed = inside2d & (zs > pz + 1e-7)
        W[i0:i0 + CH] += (crossed * S).sum(axis=1)
    return W >= 1


tray_mesh = pt.build()[0][1]
plate_mesh = pp.build()[0][1]

print("=== A. board max-back seat (what stops the board first?) ===")
WALL_THICK_IN = pl.CASE_W / 2 - pl.WALL          # 42.6 (below the 11.0 ledge)
board_back = WALL_THICK_IN                        # UART relieved: edge on wall
uart_x = (-7.79 - SHELL_W / 2, -7.79 + SHELL_W / 2)      # -12.26..-3.32
native_nose = board_back + OVH                    # 43.91
recess = 45.0 - native_nose                       # 1.09
print(f"  UART shell x {uart_x[0]:+.2f}..{uart_x[1]:+.2f} z 7.0..10.26 "
      f"overhangs into the relief pocket (x {pt.UART_X0}..{pt.UART_X1}, "
      f"floor y={pt.UART_SKIN_Y})")
print(f"  board back edge {board_back:.2f}; UART nose y {native_nose:.2f} vs "
      f"pocket floor {pt.UART_SKIN_Y} -> margin {pt.UART_SKIN_Y - native_nose:.2f}")
print(f"  native receptacle face recess behind outer wall: {recess:.2f} mm "
      f"(usable <= ~1.5) {check('usb recess', recess <= 1.5)}")

print("\n=== B. UART shell volume vs tray wall + plate skirt (mesh samples) ===")
xs = np.arange(uart_x[0] + 0.1, uart_x[1], 0.35)
ys = np.arange(WALL_THICK_IN + 0.05, native_nose, 0.18)
zs = np.arange(7.05, 10.26, 0.4)
pts = np.array([(x, y, z) for x in xs for y in ys for z in zs])
hit_t = winding_inside(tray_mesh, pts)
hit_p = winding_inside(plate_mesh, pts)
print(f"  samples in the UART-shell overhang box: {len(pts)}")
print(f"  inside TRAY  mesh: {int(hit_t.sum())} "
      f"{check('uart vs tray wall', hit_t.sum() == 0)}")
print(f"  inside PLATE mesh: {int(hit_p.sum())} "
      f"{check('uart vs plate skirt', hit_p.sum() == 0)}")

print("\n=== C. module can / antenna vs switch center posts + pins ===")
front = board_back - BRD_L                        # -20.27
can = box(-9.0, front, 9.0, front + (25.5 - 6.3))  # antenna overhangs front
ant = box(-9.0, front - 6.3, 9.0, front)
print(f"  board edge {board_back:.2f}, front {front:.2f}; can y {front:.2f}.."
      f"{front + 19.2:.2f} top Z {CAN_TOP}; ant y {front - 6.3:.2f}..{front:.2f} "
      f"top Z {ANT_TOP}")
print(f"  switch under-plate: housings Z {HOUS_BOT}, post/pin tips Z {PIN_TIP}")
over_can, over_ant = [], []
for k in pl.key_layout():
    post = Point(k["x"], k["y"]).buffer(2.0, quad_segs=16)   # d4 center post
    pins = [Point(k["x"] - 3.81, k["y"] + 2.54),
            Point(k["x"] + 2.54, k["y"] + 5.08)]
    if post.intersection(can).area > 0.01 or any(can.contains(p) for p in pins):
        over_can.append(k["id"])
    if post.intersection(ant).area > 0.01 or any(ant.contains(p) for p in pins):
        over_ant.append(k["id"])
clr_can = PIN_TIP - CAN_TOP
clr_ant = PIN_TIP - ANT_TOP
print(f"  posts/pins over the CAN: {over_can} -> clearance {clr_can:+.2f} "
      f"(need >= 0.5) {check('pins vs module can', clr_can >= 0.5)}")
print(f"  posts/pins over the ANT: {over_ant} -> clearance {clr_ant:+.2f} "
      f"(need >= 2.5) {check('pins vs antenna PCB', clr_ant >= 2.5)}")
print(f"  housings vs can: {HOUS_BOT - CAN_TOP:+.2f} "
      f"{check('housings vs can', HOUS_BOT - CAN_TOP >= 0.5)}")

print("\n=== D. Y-stop inventory (forward rib) ===")
xs = np.arange(-BRD_W / 2 + 0.4, BRD_W / 2, 0.8)
ys = np.arange(-40.0, front - 0.05, 0.4)          # ahead of the board front
pts = np.array([(x, y, z) for x in xs for y in ys for z in (5.6, 6.2, 6.8)])
hit = winding_inside(tray_mesh, pts)
stop_y = pts[hit][:, 1].max() if hit.any() else None
print(f"  tray material ahead of board front edge (board slab z 5.4..7.0): "
      f"{int(hit.sum())}/{len(pts)} samples "
      f"{check('forward y-stop exists', hit.sum() > 0)}")
if stop_y is not None:
    print(f"  nearest stop face ~y {stop_y:.2f} (rib back face {pt.RIB_Y1}, "
          f"board front {front:.2f} -> free slide {front - pt.RIB_Y1:.2f})")
print(f"  rib top {pt.RIB_TOP} vs antenna overhang bottom 7.0: "
      f"{7.0 - pt.RIB_TOP:+.2f} {check('rib clears antenna', pt.RIB_TOP <= 6.9)}")

print("\n=== E. skirt fit / screw stack / EC11 (constants + 2D) ===")
skirt = pp._skirt_profile()
bosses = unary_union([affinity.translate(pl.circle(pt.BOSS_D), sx * 39, sy * 39)
                      for sx in (-1, 1) for sy in (-1, 1)])
inter = skirt.intersection(bosses).area
gap_boss = skirt.distance(bosses)
lat = (pl.CASE_W - 2 * pt.SKIRT_WALL - pp.SKIRT_OUT_W) / 2
print(f"  skirt ∩ bosses area {inter:.3f} mm^2, radial gap {gap_boss:.2f} "
      f"{check('skirt/boss', inter < 0.01 and gap_boss >= 0.3)}")
print(f"  skirt-tray lateral gap {lat:.3f}/side "
      f"{check('skirt lateral ~0.15', 0.10 <= lat <= 0.25)}")
sk_xy = []
for poly in pl._polys(skirt):
    x0, y0, x1, y1 = poly.bounds
    for x in np.arange(x0 + 0.15, x1, 0.3):
        for y in np.arange(y0 + 0.15, y1, 0.3):
            if poly.contains(Point(x, y)):
                sk_xy.append((x + 0.013, y + 0.013))
zsk = [11.15, 12.5, 14.0, 15.5, 17.0, 17.6]
pts = np.array([(x, y, z) for x, y in sk_xy for z in zsk])
hit = winding_inside(tray_mesh, pts)
print(f"  skirt volume samples inside TRAY mesh: {int(hit.sum())}/{len(pts)} "
      f"{check('skirt vs tray mesh', hit.sum() == 0)}")

head_z = pl.PLATE_Z1 - pp.CBORE_DEPTH             # 18.2
tip_z = head_z - 8.0                              # 10.2 (M3x8)
floor_z = pt.BOSS_SOLID_TOP                       # 9.0
print(f"  M3x8: head Z {head_z:.1f}, tip Z {tip_z:.1f}, bore floor Z "
      f"{floor_z:.1f} (margin {tip_z - floor_z:+.1f}), insert zone top "
      f"{pt.BOSS_TOP:.1f} {check('screw stack', tip_z >= floor_z and tip_z <= pt.BOSS_TOP - 3)}")

free = pk.NUT_DEPTH - 0.2                         # 2.2 under the D-band
nut_top = pl.PLATE_Z1 + NUT_H                     # 21.2
ceil_w = pl.KNOB_Z0 + free                        # 22.2
print(f"  EC11 nut Ø{NUT_AF} x {NUT_H} vs recess Ø{pk.NUT_D} x {free:.1f} free: "
      f"radial {(pk.NUT_D - NUT_AF) / 2:.2f}, nut top Z {nut_top:.1f} vs recess "
      f"ceiling Z {ceil_w:.1f} {check('nut recess swallows nut', pk.NUT_D >= NUT_AF + 0.8 and ceil_w >= nut_top)}")
print(f"  knob bottom rests at Z {pl.KNOB_Z0} "
      f"{check('knob bottom at 20.0', pl.KNOB_Z0 == 20.0)}")

print("\n=== F. watertight (every mesh) ===")
wt_all = True
for name, mesh, _c in ([("tray", tray_mesh, None), ("plate", plate_mesh, None)]
                       + [(n, m, c) for n, m, c in pc.build()]
                       + pk.build()):
    rep = pl.validate(mesh)
    wt_all &= rep["watertight"]
    if not rep["watertight"]:
        print(f"  NOT WATERTIGHT: {name} {rep['problems'][:3]}")
print(f"  tray + plate + 14 caps + knob watertight: "
      f"{check('all meshes watertight', wt_all)}")

# ---------------------------------------------------------------- table ----
W = 66
print("\n" + "=" * (W + 10))
print("ACCEPTANCE TABLE")
print("=" * (W + 10))
rows = [
    (f"switch lowest Z {PIN_TIP:.1f} vs module can {CAN_TOP:.1f} "
     f"(clr {clr_can:.1f}, need >=0.5)", clr_can >= 0.5),
    (f"voice-bar pins {PIN_TIP:.1f} vs antenna PCB {ANT_TOP:.1f} "
     f"(clr {clr_ant:.1f}, need >=2.5)", clr_ant >= 2.5),
    (f"native USB recess {recess:.2f} mm behind outer wall (<= 1.5)",
     recess <= 1.5),
    (f"UART shell volume wall/skirt material: {int(hit_t.sum()) + int(hit_p.sum())} samples",
     hit_t.sum() + hit_p.sum() == 0),
    (f"skirt ∩ bosses {inter:.2f} mm^2 (gap {gap_boss:.2f}); lateral {lat:.2f}/side",
     inter < 0.01 and gap_boss >= 0.3 and 0.10 <= lat <= 0.25),
    (f"M3x8 stack: head {head_z:.1f} / tip {tip_z:.1f} / bore floor {floor_z:.1f}",
     tip_z >= floor_z and tip_z <= pt.BOSS_TOP - 3),
    (f"EC11 nut swallowed (top {nut_top:.1f} <= ceiling {ceil_w:.1f}); "
     f"knob bottom Z {pl.KNOB_Z0}", ceil_w >= nut_top and pl.KNOB_Z0 == 20.0),
    ("every mesh watertight", wt_all),
]
for text, ok in rows:
    print(f"  {'PASS' if ok else 'FAIL'}  {text}")
print("=" * (W + 10))
print(f"POST-CAN AUDIT: {len(FAILURES)} failure(s) "
      + (f"-> {FAILURES}" if FAILURES else "-> ALL CLEAR"))
sys.exit(1 if FAILURES else 0)
