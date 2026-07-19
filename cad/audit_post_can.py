"""audit_post_can.py — v4 fat-base probe (read-only): board bay seating, USB
window aperture, speaker bay, under-plate stack, and the ACCEPTANCE TABLE.

Adapted from the v3 post-raise probe; expectations updated for the v4 fat
base (+10.5 stack shift): tray 28.0 / ledge 21.5 / plate 28.0..29.5 / caps
35.0 / knob 30.5, the high board bay (shelf + bridge + locator posts at
BOARD_Z 16.0), the 26-wide USB window (17.0..23.5, through the ledge), the
down-firing speaker bay and the high mic grille. Mesh-level evidence uses
generalized-winding point sampling on the actual build() meshes. Exits
non-zero unless every check passes.

Component data (v4 hardware per SPEC):
  board: dual-USB-C ESP32-S3 clone, up to 30.0 x 64.0 x 1.6, back edge at
    Y=+42.0, underside Z 16.0 -> top 17.6; factory header pins DOWN
    (~8.5 under the PCB); header insulators ON TOP, 2.5 tall -> top 20.1;
    USB-C shells on TOP at the back edge, 8.94 w x 3.3 h -> Z 17.6..20.9
    (center 19.25), overhanging the board edge ~1.31
  plug: overmold hood 12 w x 7 t on the port axis; ~2.5 of exposed shroud
    between hood front and receptacle face when fully mated
  speaker: flange <= 72 x 42 x 1.5 ON the floor; oval driver bump up to
    50(X) x 40(Y) x 11 tall -> bump top Z 14.9
  MX: plate top->housing base 5.0 -> base Z 24.5; center post + pins 3.3
    below base -> tips Z 21.2; post d4; pins (-3.81,+2.54),(+2.54,+5.08)
  EC11: body ~12 sq x 7.0 below the plate bottom -> Z 21.0; M7 panel nut
    ~11.5 across corners x 2.2, sits on the plate top.
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

BRD_W, BRD_L, BRD_T = pl.BOARD_W, pl.BOARD_L, 1.6
BRD_BACK = 42.0
BRD_FRONT = BRD_BACK - BRD_L                   # -22.0
BRD_TOP = pl.BOARD_Z + BRD_T                   # 17.6
INSUL_TOP = BRD_TOP + 2.5                      # 20.1
SHELL_W, SHELL_H = 8.94, 3.3
CONN_OVH = 1.31
HOOD_W, HOOD_H = 12.0, 7.0
SHROUD_EXPOSED = 2.5
PIN_TIP = pl.PLATE_Z1 - 8.3                    # 21.2
HOUS_BOT = pl.PLATE_Z1 - 5.0                   # 24.5
BUMP_TOP = pl.FLOOR + 1.5 + pl.SPK_BUMP_MAX    # 14.9
NUT_AF, NUT_H = 11.5, 2.2

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


def grid_pts(x0, x1, y0, y1, zs, step=0.7):
    xs = np.arange(x0, x1 + 1e-9, step)
    ys = np.arange(y0, y1 + 1e-9, step)
    return np.array([(x, y, z) for x in xs for y in ys for z in zs])


tray_mesh = pt.build()[0][1]
plate_mesh = pp.build()[0][1]

print("=== A. board bay: drop-in volume, seats, cage ===")
pts = grid_pts(-BRD_W / 2 + 0.05, BRD_W / 2 - 0.05, BRD_FRONT + 0.05,
               BRD_BACK - 0.05, (16.05, 16.8, 17.55), 1.1)
hit = winding_inside(tray_mesh, pts)
print(f"  board slab (x ±{BRD_W / 2}, y {BRD_FRONT}..{BRD_BACK}, z 16.05..17.55): "
      f"{int(hit.sum())}/{len(pts)} samples inside tray "
      f"{check('board volume free', hit.sum() == 0)}")
shelf_pts = grid_pts(-pt.SHELF_X + 0.3, pt.SHELF_X - 0.3, pt.SHELF_Y0 + 0.1,
                     42.55, (15.9,), 0.5)
bridge_pts = grid_pts(-pt.BRIDGE_X + 0.3, pt.BRIDGE_X - 0.3, pt.BRIDGE_Y0 + 0.1,
                      pt.BRIDGE_Y1 - 0.1, (15.9,), 0.5)
hs = winding_inside(tray_mesh, shelf_pts)
hb = winding_inside(tray_mesh, bridge_pts)
print(f"  seat material at z 15.9: shelf {int(hs.sum())}/{len(shelf_pts)}, "
      f"bridge {int(hb.sum())}/{len(bridge_pts)} "
      f"{check('seats at BOARD_Z', hs.all() and hb.all())}")
tangent = abs(pt.POST_XY[0][0]) - pt.POST_D / 2
print(f"  locator posts: inner tangent ±{tangent:.1f} vs board ±{BRD_W / 2} -> "
      f"{tangent - BRD_W / 2:.2f}/side; tops {pt.POST_TOP} = board top {BRD_TOP:.1f} "
      f"+ {pt.POST_TOP - BRD_TOP:.1f} "
      f"{check('posts cage board', 0.05 <= tangent - BRD_W / 2 <= 0.3 and pt.POST_TOP - BRD_TOP >= 1.0)}")
pts = grid_pts(-BRD_W / 2 + 0.05, BRD_W / 2 - 0.05, pt.BRIDGE_Y1 + 0.05,
               pt.SHELF_Y0 - 0.05, (2.45, 6.0, 9.5, 13.0, 15.95), 1.3)
hit = winding_inside(tray_mesh, pts)
print(f"  wiring bay under the board (y {pt.BRIDGE_Y1}..{pt.SHELF_Y0}, floor->16.0 "
      f"= {pl.BOARD_Z - pl.FLOOR:.1f}): {int(hit.sum())}/{len(pts)} samples inside "
      f"{check('13.6 wiring bay open', hit.sum() == 0)}")

print("\n=== B. USB window: aperture, band, plug (mesh + analytics) ===")
pts = grid_pts(-pt.WIN_W / 2 + 0.05, pt.WIN_W / 2 - 0.05, 42.65, 44.95,
               (17.05, 18.5, 20.25, 22.0, 23.45), 0.8)
hit = winding_inside(tray_mesh, pts)
win_open = hit.sum() == 0
print(f"  aperture corridor (x ±{pt.WIN_W / 2}, through both wall columns, "
      f"z 17.05..23.45): {int(hit.sum())}/{len(pts)} samples inside "
      f"{check('window open through wall', win_open)}")
edge = np.array([(0, 44.4, 16.95), (0, 44.4, 23.55),
                 (-13.05, 44.4, 20.25), (13.05, 44.4, 20.25)])
he = winding_inside(tray_mesh, edge)
print(f"  wall present just outside the window edges (sill/ceiling/jambs): "
      f"{int(he.sum())}/4 {check('window edges exact', he.all())}")
shell_z0, shell_z1 = BRD_TOP, BRD_TOP + SHELL_H
print(f"  shell band z {shell_z0:.1f}..{shell_z1:.1f} (center "
      f"{(shell_z0 + shell_z1) / 2:.2f}) in window {pt.WIN_Z0}..{pt.WIN_Z1}: margins "
      f"{shell_z0 - pt.WIN_Z0:.1f}/{pt.WIN_Z1 - shell_z1:.1f} "
      f"{check('shell inside window band', shell_z0 - pt.WIN_Z0 >= 0.3 and pt.WIN_Z1 - shell_z1 >= 0.3)}")
recess = pl.CASE_W / 2 - (BRD_BACK + CONN_OVH)
print(f"  hood {HOOD_W:.0f}x{HOOD_H:.0f} vs aperture {pt.WIN_W:.0f}x"
      f"{pt.WIN_Z1 - pt.WIN_Z0:.1f}: width play {(pt.WIN_W - HOOD_W) / 2:.1f}/side "
      f"(port offsets to ±{pt.WIN_W / 2 - HOOD_W / 2:.1f}); receptacle recess "
      f"{recess:.2f} <= {SHROUD_EXPOSED} exposed shroud -> mates at the mouth "
      f"{check('plug hood passes aperture', HOOD_W <= pt.WIN_W - 2 and recess <= SHROUD_EXPOSED)}")
sk = grid_pts(-pt.WIN_W / 2 + 0.05, pt.WIN_W / 2 - 0.05, 42.55, 43.6,
              (21.55, 23.4, 25.5, 27.9), 0.8)   # ledge..under the plate slab
hp = winding_inside(plate_mesh, sk)
print(f"  plate-skirt material in the window corridor (ledge..plate slab): "
      f"{int(hp.sum())}/{len(sk)} samples "
      f"{check('back skirt notch clears window', hp.sum() == 0)}")

print("\n=== C. under-plate stack over the bay ===")
board_rect = box(-BRD_W / 2, BRD_FRONT, BRD_W / 2, BRD_BACK)
strips = unary_union([box(BRD_W / 2 - 2.5, BRD_FRONT, BRD_W / 2, BRD_BACK),
                      box(-BRD_W / 2, BRD_FRONT, -BRD_W / 2 + 2.5, BRD_BACK)])
over_b, over_s = [], []
for k in pl.key_layout():
    post = Point(k["x"], k["y"]).buffer(2.0, quad_segs=16)
    pins = [Point(k["x"] - 3.81, k["y"] + 2.54), Point(k["x"] + 2.54, k["y"] + 5.08)]
    if unary_union([post] + pins).intersects(board_rect):
        over_b.append(k["id"])
    if any(strips.contains(p) for p in pins) or post.intersects(strips):
        over_s.append(k["id"])
clr_ins = PIN_TIP - INSUL_TOP
print(f"  switch lowest Z {PIN_TIP:.1f}; housings {HOUS_BOT:.1f}; board top "
      f"{BRD_TOP:.1f}; insulator top {INSUL_TOP:.1f}")
print(f"  keys over board {over_b}; over insulator strips {over_s}")
print(f"  pins vs insulators: {clr_ins:+.1f} (need >= 0.8) "
      f"{check('pins vs insulators', clr_ins >= 0.8)}")
print(f"  pins vs bare board: {PIN_TIP - BRD_TOP:+.1f} "
      f"{check('pins vs board', PIN_TIP - BRD_TOP >= 0.5)}")
print(f"  housings vs insulators: {HOUS_BOT - INSUL_TOP:+.1f} "
      f"{check('housings vs insulators', HOUS_BOT - INSUL_TOP >= 0.5)}")
ec_bot = pl.PLATE_Z0 - 7.0
ec_body = affinity.translate(box(-6.0, -6.0, 6.0, 6.0), *pl.KNOB_POS)
d_ec = ec_body.distance(board_rect)
print(f"  EC11 body (12 sq, bottom Z {ec_bot:.1f}) at x {pl.KNOB_POS[0]:.2f}: "
      f"lateral gap to board {d_ec:.2f} "
      f"{check('EC11 body clear of board', d_ec >= 0.5 or ec_bot - BRD_TOP >= 0.5)}")

print("\n=== D. speaker bay: grille, pilots, bump (mesh + analytics) ===")
slots = pt.spk_floor_opening()
slot_ok = True
for poly in pl._polys(slots):
    c = poly.representative_point()
    ppts = np.array([(c.x, c.y, z) for z in (0.1, 1.2, 2.3)]
                    + [(c.x + 6, c.y, 1.2), (c.x - 6, c.y, 1.2)])
    slot_ok &= not winding_inside(tray_mesh, ppts).any()
print(f"  3 grille slots open through both floor layers: "
      f"{check('slots open', slot_ok and len(pl._polys(slots)) == 3)}")
bar_pts = np.array([(0, -25.333, 1.2), (0, -16.667, 1.2), (0, -25.333, 0.1),
                    (0, -16.667, 2.3)])
hbar = winding_inside(tray_mesh, bar_pts)
print(f"  grille bars present (full floor thickness): {int(hbar.sum())}/4 "
      f"{check('grille bars', hbar.all())}")
pil_pts = np.array([(x, y, z) for x, y in pt.SPK_PILOT_XY for z in (0.1, 1.2, 2.3)])
hpil = winding_inside(tray_mesh, pil_pts)
print(f"  pilot bores open through the floor: {int(hpil.sum())}/{len(pil_pts)} "
      f"{check('pilots open', hpil.sum() == 0)}")
feet_pts = np.array([(sx * 36, sy * 36, 0.3) for sx in (-1, 1) for sy in (-1, 1)]
                    + [(sx * 36, sy * 36, 0.75) for sx in (-1, 1) for sy in (-1, 1)])
hf = winding_inside(tray_mesh, feet_pts)
print(f"  feet recesses: open below 0.6 ({int(hf[:4].sum())}/4 hits), ceiling "
      f"intact above ({int(hf[4:].sum())}/4 hits) "
      f"{check('feet-recess layers intact', hf[:4].sum() == 0 and hf[4:].all())}")
print(f"  bump top {BUMP_TOP:.1f} vs board underside {pl.BOARD_Z:.1f}: "
      f"{pl.BOARD_Z - BUMP_TOP:+.1f} (need >= 1.0) "
      f"{check('bump vs board underside', pl.BOARD_Z - BUMP_TOP >= 1.0)}")
bump = affinity.translate(affinity.scale(pl.circle(2.0), 25.0, 20.0), *pl.SPK_CENTER)
bridge2d = box(-pt.BRIDGE_X, pt.BRIDGE_Y0, pt.BRIDGE_X, pt.BRIDGE_Y1)
print(f"  oval bump (<=50x40) vs bridge wall: plan gap {bump.distance(bridge2d):.1f} "
      f"{check('bump clears bridge', bump.distance(bridge2d) >= 2.0)}")
tip_below = 6.0 - 1.5 - pl.FLOOR
print(f"  M2.5x6 tips {tip_below:.1f} under the floor; >=3mm feet stand the case "
      f"{3.0 - pt.FEET_DEPTH:.1f} off the desk -> {3.0 - pt.FEET_DEPTH - tip_below:.1f} "
      f"ground clearance {check('screw tips in foot gap', 3.0 - pt.FEET_DEPTH - tip_below >= 0.2)}")

print("\n=== E. amp pocket / wire posts / mic grille (mesh) ===")
pk_pts = grid_pts(pt.AMP_C[0] - 9.95, pt.AMP_C[0] + 9.95, pt.AMP_C[1] - 9.95,
                  pt.AMP_C[1] + 9.95, (2.45, 3.3, 4.35), 1.0)
hpk = winding_inside(tray_mesh, pk_pts)
ridge_pts = np.array([(41.7, 24.7, 3.3), (41.7, 3.3, 3.3),
                      (20.3, 24.7, 3.3), (20.3, 3.3, 3.3)])
hr = winding_inside(tray_mesh, ridge_pts)
print(f"  20x20 pocket interior free above the floor: {int(hpk.sum())}/{len(pk_pts)}; "
      f"corner ridges present {int(hr.sum())}/4 "
      f"{check('amp pocket', hpk.sum() == 0 and hr.all())}")
wp_ok = True
for x, y in pt.WPOST_XY:
    open_pts = np.array([(x, y, 4.0), (x + 2.0, y, 4.0), (x - 2.0, y, 4.0)])
    solid_pts = np.array([(x, y + 2.0, 4.0), (x, y - 2.0, 4.0), (x, y, 2.6),
                          (x, y, 7.5), (x, y, 10.3)])
    wp_ok &= not winding_inside(tray_mesh, open_pts).any()
    wp_ok &= winding_inside(tray_mesh, solid_pts).all()
top_pts = np.array([(x, y, 10.5) for x, y in pt.WPOST_XY])
wp_ok &= not winding_inside(tray_mesh, top_pts).any()
print(f"  wire posts: zip-tie notches open through, slivers + shaft solid, "
      f"tops at {pl.FLOOR + pt.WPOST_H:.1f} {check('wire posts', wp_ok)}")
mic_ok = True
for x in pt.MIC_XS:
    open_pts = np.array([(x, -44.4, 20.15), (x, -42.75, 20.15), (x, -44.9, 20.15)])
    mic_ok &= not winding_inside(tray_mesh, open_pts).any()
edge_pts = np.array([(-20, -44.4, 19.3), (-20, -44.4, 21.0),
                     (-14.9, -44.4, 20.15), (-25.1, -44.4, 20.15)])
mic_ok &= winding_inside(tray_mesh, edge_pts).all()
print(f"  mic ports open through both columns, walls exact around them "
      f"{check('mic grille', mic_ok)}")
print(f"  mic grille fully below the ledge: {pt.MIC_Z1} + 0.6 = {pl.LEDGE_Z} "
      f"{check('mic below ledge', pl.LEDGE_Z - pt.MIC_Z1 >= 0.5)}")

print("\n=== F. skirt fit / screw stack / EC11 (constants + 2D + mesh) ===")
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
zsk = [21.65, 23.0, 24.5, 26.0, 27.5, 28.1]
pts = np.array([(x, y, z) for x, y in sk_xy for z in zsk])
hit = winding_inside(tray_mesh, pts)
print(f"  skirt volume samples inside TRAY mesh: {int(hit.sum())}/{len(pts)} "
      f"{check('skirt vs tray mesh', hit.sum() == 0)}")

head_z = pl.PLATE_Z1 - pp.CBORE_DEPTH             # 28.7
tip_z = head_z - 8.0                              # 20.7 (M3x8)
floor_z = pt.BOSS_SOLID_TOP                       # 19.5
print(f"  M3x8: head Z {head_z:.1f}, tip Z {tip_z:.1f}, bore floor Z "
      f"{floor_z:.1f} (margin {tip_z - floor_z:+.1f}), insert zone top "
      f"{pt.BOSS_TOP:.1f} {check('screw stack', tip_z >= floor_z and tip_z <= pt.BOSS_TOP - 3)}")

free = pk.NUT_DEPTH - 0.2                         # 2.2 under the D-band
nut_top = pl.PLATE_Z1 + NUT_H                     # 31.7
ceil_w = pl.KNOB_Z0 + free                        # 32.7
print(f"  EC11 nut Ø{NUT_AF} x {NUT_H} vs recess Ø{pk.NUT_D} x {free:.1f} free: "
      f"radial {(pk.NUT_D - NUT_AF) / 2:.2f}, nut top Z {nut_top:.1f} vs recess "
      f"ceiling Z {ceil_w:.1f} {check('nut recess swallows nut', pk.NUT_D >= NUT_AF + 0.8 and ceil_w >= nut_top)}")
print(f"  knob bottom rests at Z {pl.KNOB_Z0} "
      f"{check('knob bottom at 30.5', pl.KNOB_Z0 == 30.5)}")

print("\n=== G. watertight (every mesh) ===")
wt_all = True
for name, mesh, _c in ([("tray", tray_mesh, None), ("plate", plate_mesh, None)]
                       + [(n, m, c) for n, m, c in pc.build()]
                       + pk.build()):
    rep = pl.validate(mesh)
    wt_all &= rep["watertight"]
    if not rep["watertight"]:
        print(f"  NOT WATERTIGHT: {name} {rep['problems'][:3]}")
print(f"  tray + plate + 14 caps (+legends) + knob watertight: "
      f"{check('all meshes watertight', wt_all)}")

# ---------------------------------------------------------------- table ----
W = 66
print("\n" + "=" * (W + 10))
print("ACCEPTANCE TABLE (v4 fat base)")
print("=" * (W + 10))
rows = [
    (f"switch lowest Z {PIN_TIP:.1f} vs header insulator top {INSUL_TOP:.1f} "
     f"(clr {clr_ins:.1f}, need >=0.8)", clr_ins >= 0.8),
    (f"speaker bump top {BUMP_TOP:.1f} vs board underside {pl.BOARD_Z:.1f} "
     f"(clr {pl.BOARD_Z - BUMP_TOP:.1f}, need >=1.0)",
     pl.BOARD_Z - BUMP_TOP >= 1.0),
    (f"USB window 26x6.5 @ Z {pt.WIN_Z0}..{pt.WIN_Z1}: aperture open, shell "
     f"band inside, hood mates (recess {recess:.2f})",
     win_open and shell_z0 - pt.WIN_Z0 >= 0.3 and recess <= SHROUD_EXPOSED),
    (f"board bay: slab free, seats @16.0, posts cage {tangent - BRD_W / 2:.2f}/side, "
     f"13.6 wiring bay open",
     not [f for f in FAILURES if f in (
         'board volume free', 'seats at BOARD_Z', 'posts cage board',
         '13.6 wiring bay open')]),
    (f"skirt ∩ bosses {inter:.2f} mm^2 (gap {gap_boss:.2f}); lateral {lat:.2f}/side; "
     f"back notch clears the window band",
     inter < 0.01 and gap_boss >= 0.3 and 0.10 <= lat <= 0.25
     and 'back skirt notch clears window' not in FAILURES),
    (f"M3x8 stack: head {head_z:.1f} / tip {tip_z:.1f} / bore floor {floor_z:.1f} "
     f"(margin {tip_z - floor_z:+.1f}, insert top {pt.BOSS_TOP:.1f})",
     tip_z >= floor_z and tip_z <= pt.BOSS_TOP - 3),
    (f"EC11 body (bottom {ec_bot:.1f}) clear of board (lateral {d_ec:.1f}); "
     f"nut swallowed; knob at Z {pl.KNOB_Z0}",
     (d_ec >= 0.5) and ceil_w >= nut_top and pl.KNOB_Z0 == 30.5),
    ("speaker floor: slots+pilots open, grille bars + feet-recess layers intact",
     not [f for f in FAILURES if f in (
         'slots open', 'grille bars', 'pilots open', 'feet-recess layers intact')]),
    ("every mesh watertight", wt_all),
]
for text, ok in rows:
    print(f"  {'PASS' if ok else 'FAIL'}  {text}")
print("=" * (W + 10))
print(f"POST-CAN AUDIT: {len(FAILURES)} failure(s) "
      + (f"-> {FAILURES}" if FAILURES else "-> ALL CLEAR"))
sys.exit(1 if FAILURES else 0)
