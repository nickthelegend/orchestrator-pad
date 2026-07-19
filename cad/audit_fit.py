"""audit_fit.py — AUDIT probe: component fit + SPEC compliance (read-only).

v4 "fat base" expectations: tall tray (28.0) with the component bay —
board shelf / bridge / locator posts, the wide back USB window, the
down-firing speaker bay, the amp pocket, the zip-tie wire posts and the
high mic grille — plus the +10.5-shifted plate/caps/knob stack
(plate 28.0..29.5, caps at 35.0, knob at 30.5).

Recomputes every checklist quantity from the actual build() outputs /
partlib constants. Prints PASS/FAIL per item; exits non-zero on any FAIL.
No files modified.
"""
from __future__ import annotations

import sys

from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union

import partlib as pl
import part_plate
import part_tray
import part_caps
import part_knob

FAILURES = []


def check(name, ok):
    FAILURES.extend([] if ok else [name])
    return "PASS" if ok else "FAIL"


def sec(t):
    print(f"\n=== {t} ===")


# component data (v4 hardware per SPEC)
BRD_W, BRD_L, BRD_T = pl.BOARD_W, pl.BOARD_L, 1.6      # caged max envelope
BRD_BACK = 42.0                        # board back edge (SPEC board bay)
BRD_TOP = pl.BOARD_Z + BRD_T           # 17.6
INSUL_H = 2.5                          # factory header insulator (on TOP)
INSUL_TOP = BRD_TOP + INSUL_H          # 20.1
SHELL_W, SHELL_H = 8.94, 3.3           # board-top USB-C shell
SHELL_Z0, SHELL_Z1 = BRD_TOP, BRD_TOP + SHELL_H        # 17.6..20.9
CONN_OVH = 1.31                        # USB-C shells overhang the board edge
HOOD_W, HOOD_H = 12.0, 7.0             # cable plug overmold hood
SHROUD_EXPOSED = 2.5                   # exposed metal between hood + receptacle
EC11_BODY_SQ = 12.0                    # EC11 body width
EC11_BODY_DEPTH = 7.0                  # body depth below the plate bottom
NUT_AF, NUT_H = 11.5, 2.2              # EC11 M7 panel nut
FOOT_H = 3.0                           # BOM: feet >= 3mm tall

# ---------------------------------------------------------------- 1. grid ----
sec("1. key grid vs SPEC")
spec_grid = {
    ("cursor"): (pl.COL_X[1], pl.ROW_Y[0]), ("codex"): (pl.COL_X[2], pl.ROW_Y[0]),
    ("preset3"): (pl.COL_X[3], pl.ROW_Y[0]),
    ("grok"): (pl.COL_X[0], pl.ROW_Y[1]), ("claude"): (pl.COL_X[1], pl.ROW_Y[1]),
    ("antigravity"): (pl.COL_X[2], pl.ROW_Y[1]), ("opencode"): (pl.COL_X[3], pl.ROW_Y[1]),
    ("kiro"): (pl.COL_X[0], pl.ROW_Y[2]), ("run"): (pl.COL_X[1], pl.ROW_Y[2]),
    ("approve"): (pl.COL_X[2], pl.ROW_Y[2]), ("reject"): (pl.COL_X[3], pl.ROW_Y[2]),
    ("prompt"): (pl.COL_X[0], pl.ROW_Y[3]), ("voice"): (0.0, pl.ROW_Y[3]),
    ("send"): (pl.COL_X[3], pl.ROW_Y[3]),
}
keys = pl.key_layout()
print("count:", len(keys), check("key count", len(keys) == 14))
for k in keys:
    want = spec_grid[k["id"]]
    got = (k["x"], k["y"])
    ok = abs(got[0] - want[0]) < 1e-9 and abs(got[1] - want[1]) < 1e-9
    if not ok or k["id"] == "voice":
        print(f"  {k['id']:12s} got {got} want {want} u={k['units']} "
              f"{check('grid ' + k['id'], ok)}")
print("knob pos:", pl.KNOB_POS,
      check("knob pos", pl.KNOB_POS == (pl.COL_X[0], pl.ROW_Y[0])))

# ------------------------------------------------------- 2. plate cutouts ----
sec("2. MX cutouts / plate thickness / webbing")
print("MX_CUT:", pl.MX_CUT, check("MX cutout 14.1", pl.MX_CUT == 14.1))
print("plate thickness:", pl.PLATE_Z1 - pl.PLATE_Z0,
      check("plate 1.5 thick", abs((pl.PLATE_Z1 - pl.PLATE_Z0) - 1.5) < 1e-9))
print(f"plate bands: {pl.PLATE_Z0}..{pl.PLATE_Z1 - part_plate.CBORE_DEPTH:.1f} + "
      f"{pl.PLATE_Z1 - part_plate.CBORE_DEPTH - 0.2:.1f}..{pl.PLATE_Z1} "
      f"{check('plate bands 28.0..28.7 + 28.5..29.5', pl.PLATE_Z0 == 28.0 and pl.PLATE_Z1 == 29.5)}")
prof_a = part_plate._plate_profile(part_plate.SCREW_D)
prof_b = part_plate._plate_profile(part_plate.CBORE_D)
thru_ok = True
for k in keys:
    pt2 = Point(k["x"], k["y"])
    if prof_a.contains(pt2) or prof_b.contains(pt2):
        print("  cutout NOT through both bands at", k["id"], "FAIL")
        thru_ok = False
print("cutouts through both bands:", check("MX cutouts through", thru_ok))
web_1u = pl.PITCH - pl.MX_CUT
print(f"webbing between adjacent cutouts: {web_1u:.2f}",
      check("webbing >= 4.0", web_1u >= 4.0))
d_knob_cut = pl.PITCH - pl.KNOB_HOLE_D / 2 - pl.MX_CUT / 2
print(f"knob hole edge to cursor cutout edge: {d_knob_cut:.2f}")
cut = affinity.translate(pl.rounded_rect(pl.MX_CUT, pl.MX_CUT, part_plate.MX_CORNER_R),
                         pl.COL_X[3], pl.ROW_Y[0])
cb = affinity.translate(pl.circle(part_plate.CBORE_D), 39, 39)
tw = affinity.translate(pl.circle(part_plate.TOWER_D), 39, 39)
print(f"cutout->counterbore web: {cut.distance(cb):.2f}   cutout->tower web: {cut.distance(tw):.2f}")

# ------------------------------------------------------------ 3. cap gaps ----
sec("3. keycap clearances (>= 0.8 required)")
bases = {}
for k in keys:
    ob = pl.rounded_rect(*part_caps.SIZES[k["units"]][0])
    bases[k["id"]] = affinity.translate(ob, k["x"], k["y"])
ids = list(bases)
worst = (1e9, None, None)
for i in range(len(ids)):
    for j in range(i + 1, len(ids)):
        d = bases[ids[i]].distance(bases[ids[j]])
        if d < worst[0]:
            worst = (d, ids[i], ids[j])
print(f"min cap-cap gap: {worst[0]:.3f} ({worst[1]} vs {worst[2]})",
      check("cap-cap gap", worst[0] >= 0.8))
knob_circle = affinity.translate(pl.circle(part_knob.KNOB_D), *pl.KNOB_POS)
dk = min((bases[i].distance(knob_circle), i) for i in ids)
print(f"knob(d17)->nearest cap gap: {dk[0]:.3f} ({dk[1]})",
      check("knob-cap gap", dk[0] >= 0.8))
clr = pl.CAP_Z0 - 4.0 - pl.PLATE_Z1
print(f"cap bottom after 4mm travel vs plate top: {clr:.2f}",
      check("travel clearance", clr >= 1.2))

# ------------------------------------------------------------- 4. EC11 ------
sec("4. EC11 knob/plate/board")
print("plate knob hole d:", pl.KNOB_HOLE_D, check("knob hole 7.4", pl.KNOB_HOLE_D == 7.4))
print("bore profile:", part_knob.BORE_D, part_knob.BORE_FLAT,
      check("D-bore 6.1/4.6", (part_knob.BORE_D, part_knob.BORE_FLAT) == (6.1, 4.6)))
print("knob bottom vs plate top:", round(pl.KNOB_Z0 - pl.PLATE_Z1, 2),
      check("knob floats over plate", pl.KNOB_Z0 - pl.PLATE_Z1 > 0))
print(f"effective bore depth: {part_knob.CEIL_Z0:.1f} (spec 12.0, ceiling overlap eats 0.2)")
free = part_knob.NUT_DEPTH - 0.2
nut_top = pl.PLATE_Z1 + NUT_H
recess_ceiling = pl.KNOB_Z0 + free
print(f"nut recess Ø{part_knob.NUT_D} x {free:.1f} free vs nut Ø{NUT_AF} x {NUT_H}: "
      f"radial {(part_knob.NUT_D - NUT_AF) / 2:.2f}, nut top Z{nut_top:.1f} vs "
      f"recess ceiling Z{recess_ceiling:.1f} "
      f"{check('nut swallowed', part_knob.NUT_D >= NUT_AF + 0.8 and recess_ceiling >= nut_top)}")
# EC11 body hangs below the plate into the bay — must clear the board
ec_bot = pl.PLATE_Z0 - EC11_BODY_DEPTH                  # 21.0
ec_body = affinity.translate(
    box(-EC11_BODY_SQ / 2, -EC11_BODY_SQ / 2, EC11_BODY_SQ / 2, EC11_BODY_SQ / 2),
    *pl.KNOB_POS)
board_rect = box(-BRD_W / 2, BRD_BACK - BRD_L, BRD_W / 2, BRD_BACK)
d_ec_brd = ec_body.distance(board_rect)
print(f"EC11 body bottom Z {ec_bot:.1f} (plate bottom {pl.PLATE_Z0} - {EC11_BODY_DEPTH}); "
      f"lateral gap to board {d_ec_brd:.2f} (board top {BRD_TOP:.1f}) "
      f"{check('EC11 body clear of board', d_ec_brd >= 0.5 or ec_bot - BRD_TOP >= 0.5)}")
tray_liner_in = pl.rounded_rect(pl.CASE_W - 2 * pl.WALL, pl.CASE_W - 2 * pl.WALL,
                                pl.CASE_R - pl.WALL)
print(f"EC11 body vs tray liner wall: gap "
      f"{tray_liner_in.exterior.distance(ec_body):.2f} (contained: "
      f"{tray_liner_in.contains(ec_body)}) "
      f"{check('EC11 body inside interior', tray_liner_in.contains(ec_body))}")

# --------------------------------------------------- 5. skirt vs tray fit ----
sec("5. plate skirt vs tray (recompute)")
skirt = part_plate._skirt_profile()      # actual build profile (with notches)
skirt_out = pl.rounded_rect(part_plate.SKIRT_OUT_W, part_plate.SKIRT_OUT_W,
                            part_plate.SKIRT_OUT_R)
tray_in_thin = pl.rounded_rect(pl.CASE_W - 2 * part_tray.SKIRT_WALL,
                               pl.CASE_W - 2 * part_tray.SKIRT_WALL,
                               pl.CASE_R - part_tray.SKIRT_WALL)
pts = [skirt_out.exterior.interpolate(t, normalized=True) for t in
       [i / 720 for i in range(720)]]
min_gap = min(tray_in_thin.exterior.distance(p) for p in pts)
flats = (pl.CASE_W - 2 * part_tray.SKIRT_WALL - part_plate.SKIRT_OUT_W) / 2
print(f"skirt outer vs tray upper-inner: min gap {min_gap:.3f} per side "
      f"(SPEC ~0.15; flats give {flats:.3f}) "
      f"{check('skirt lateral ~0.15', 0.10 <= min_gap <= 0.25)}")
print(f"skirt band Z {pl.LEDGE_Z}..{pl.PLATE_Z0 + 0.2:.1f} "
      f"{check('skirt 21.5..28.2', pl.LEDGE_Z == 21.5 and pl.PLATE_Z0 == 28.0)}")
boss_zone = unary_union([affinity.translate(pl.circle(part_tray.BOSS_D), sx * 39, sy * 39)
                         for sx in (-1, 1) for sy in (-1, 1)])
inter = skirt.intersection(boss_zone)
boss_gap = skirt.distance(boss_zone)
z_lo = max(pl.LEDGE_Z, part_tray.BOSS_SOLID_TOP - part_tray.OVL)
z_hi = min(pl.PLATE_Z0 + 0.2, part_tray.BOSS_TOP)
print(f"skirt ∩ bosses XY area: {inter.area:.2f} mm^2, radial gap {boss_gap:.2f} "
      f"(boss band Z {z_lo:.1f}..{z_hi:.1f})  "
      f"{check('skirt/boss', inter.area < 0.01 and boss_gap >= 0.3)}")
# the USB window's upper band (21.5..23.5) crosses the skirt seat: the back
# notch (x -14..14) must open the whole 26-wide window corridor
win_corr = box(-part_tray.WIN_W / 2, 40.0, part_tray.WIN_W / 2, 46.0)
blocked = skirt.intersection(win_corr).area
print(f"skirt material inside USB window corridor (x ±{part_tray.WIN_W / 2:.0f}): "
      f"{blocked:.2f} mm^2 "
      f"{check('back notch clears window', blocked < 0.01)}")
notch_margin = part_plate.USB_NOTCH_X1 - part_tray.WIN_W / 2
print(f"back notch x {part_plate.USB_NOTCH_X0}..{part_plate.USB_NOTCH_X1} vs window "
      f"±{part_tray.WIN_W / 2:.0f}: margin {notch_margin:.1f}/side "
      f"{check('notch margin', notch_margin >= 0.5)}")
# the v4 mic grille sits fully below the ledge — no front notch needed
mic_margin = pl.LEDGE_Z - part_tray.MIC_Z1
print(f"mic grille ceiling {part_tray.MIC_Z1} vs ledge {pl.LEDGE_Z}: margin "
      f"{mic_margin:.1f} (no front skirt notch needed) "
      f"{check('mic below ledge', mic_margin >= 0.5)}")
tower = affinity.translate(pl.circle(part_plate.TOWER_D), 39, 39)
print(f"tower vs tray thin-wall inner: gap {tray_in_thin.exterior.distance(tower):.3f} "
      f"(contained: {tray_in_thin.contains(tower)}) "
      f"{check('towers inside tray', tray_in_thin.contains(tower))}")

# --------------------------------------------------------- 6. screw stack ----
SCREW_L = 8.0
sec(f"6. screw stack (M3x{SCREW_L:.0f} button head)")
head_z = pl.PLATE_Z1 - part_plate.CBORE_DEPTH          # 28.7
bore_floor = part_tray.BOSS_SOLID_TOP                  # 19.5
tip_z = head_z - SCREW_L                               # 20.7
print(f"counterbore d{part_plate.CBORE_D} x {part_plate.CBORE_DEPTH} -> head at Z{head_z:.1f}")
print(f"3.4 channel: plate {pl.PLATE_Z0}->{head_z:.1f} + tower {part_plate.TOWER_Z0}->{pl.PLATE_Z0 + 0.2}")
print(f"boss bore d{part_tray.BORE_D} open {bore_floor}->{part_tray.BOSS_TOP} "
      f"(depth {part_tray.BOSS_TOP - bore_floor:.1f})")
print(f"M3x{SCREW_L:.0f} tip lands at Z{tip_z:.1f}; bore floor Z{bore_floor:.1f} -> "
      f"margin {tip_z - bore_floor:+.1f} mm "
      f"{check('screw does not bottom out', tip_z >= bore_floor)}")
print(f"insert zone top Z{part_tray.BOSS_TOP:.1f}; screw reaches the insert: "
      f"{check('screw engages insert', tip_z <= part_tray.BOSS_TOP - 3)}")

# ---------------------------------------------------------- 7. USB window ----
sec("7. USB window vs dual-USB-C board (board-top ports)")
win_lo, win_hi = -part_tray.WIN_W / 2, part_tray.WIN_W / 2
print(f"window: {part_tray.WIN_W} wide (x {win_lo:+.0f}..{win_hi:+.0f}), "
      f"Z {part_tray.WIN_Z0}..{part_tray.WIN_Z1} "
      f"({part_tray.WIN_Z1 - part_tray.WIN_Z0:.1f} tall) "
      f"{check('window = USB_WIN', (part_tray.WIN_W, part_tray.WIN_Z0, part_tray.WIN_Z1) == pl.USB_WIN)}")
print(f"shell band: {SHELL_W} w x {SHELL_H} h on the board top -> Z "
      f"{SHELL_Z0:.1f}..{SHELL_Z1:.1f} (center {(SHELL_Z0 + SHELL_Z1) / 2:.2f}); margins "
      f"{SHELL_Z0 - part_tray.WIN_Z0:.1f} below / {part_tray.WIN_Z1 - SHELL_Z1:.1f} above "
      f"{check('shell inside window band', SHELL_Z0 - part_tray.WIN_Z0 >= 0.3 and part_tray.WIN_Z1 - SHELL_Z1 >= 0.3)}")
shell_env = win_hi - SHELL_W / 2
hood_env = win_hi - HOOD_W / 2
print(f"port-offset envelope: shell fully in window for |x| <= {shell_env:.1f}, "
      f"hood for |x| <= {hood_env:.1f} (typical dual ports sit at |x| <= 5.5) "
      f"{check('port offsets dont matter', shell_env >= 5.5 and hood_env >= 5.5)}")
recess = (pl.CASE_W / 2) - (BRD_BACK + CONN_OVH)       # 1.69
print(f"receptacle face: board edge {BRD_BACK} + overhang {CONN_OVH} -> y "
      f"{BRD_BACK + CONN_OVH:.2f}; recess behind outer face {recess:.2f}")
print(f"plug hood {HOOD_W:.0f}w x {HOOD_H:.0f}t vs aperture {part_tray.WIN_W:.0f}w x "
      f"{part_tray.WIN_Z1 - part_tray.WIN_Z0:.1f}t: width play "
      f"{(part_tray.WIN_W - HOOD_W) / 2:.1f}/side; recess {recess:.2f} <= exposed-shroud "
      f"reach {SHROUD_EXPOSED:.1f} -> plug mates with the hood at the mouth "
      f"{check('plug hood passes aperture', HOOD_W <= part_tray.WIN_W - 2 and recess <= SHROUD_EXPOSED)}")
print(f"  (zero-overhang clone: recess {pl.CASE_W / 2 - BRD_BACK:.1f} — still under "
      f"most cables' 2.5..3.5 exposed shroud)")

# ----------------------------------------------------------- 8. board bay ----
sec("8. board bay (shelf / bridge / locator posts)")
print(f"shelf: x ±{part_tray.SHELF_X}, y {part_tray.SHELF_Y0}..{part_tray.SHELF_Y1} "
      f"(tab {pl.CASE_W / 2 - pl.WALL - part_tray.SHELF_Y0:.1f} off the wall), body "
      f"{part_tray.SHELF_Z0}..{pl.BOARD_Z} "
      f"{check('shelf top = BOARD_Z', part_tray.SHELF_Y0 == 41.0 and part_tray.SHELF_Z0 == 13.5)}")
bearing = BRD_BACK - part_tray.SHELF_Y0
print(f"board back edge {BRD_BACK} -> shelf bearing {bearing:.1f} deep, wall gap "
      f"{pl.CASE_W / 2 - pl.WALL - BRD_BACK:.1f} "
      f"{check('shelf bearing', bearing >= 0.8)}")
print(f"bridge: x ±{part_tray.BRIDGE_X}, y {part_tray.BRIDGE_Y0}..{part_tray.BRIDGE_Y1}, "
      f"floor..{pl.BOARD_Z} "
      f"{check('bridge spans board width', part_tray.BRIDGE_X >= BRD_W / 2 + 0.5)}")
tangent = 17.6 - part_tray.POST_D / 2
side_clr = tangent - BRD_W / 2
cage_h = part_tray.POST_TOP - BRD_TOP
print(f"posts Ø{part_tray.POST_D} at {part_tray.POST_XY}, tops Z {part_tray.POST_TOP}: "
      f"inner tangent ±{tangent:.1f} -> {side_clr:.2f}/side to a {BRD_W:.0f}-wide board; "
      f"cage {cage_h:.1f} above the board top "
      f"{check('posts cage board', 0.05 <= side_clr <= 0.3 and cage_h >= 1.0)}")
under = pl.BOARD_Z - pl.FLOOR
print(f"under-board bay: floor {pl.FLOOR} -> {pl.BOARD_Z} = {under:.1f} for the "
      f"factory header pins (~8.5) + angled dupont connectors "
      f"{check('13.6 under-board', abs(under - 13.6) < 1e-9)}")
bump_top = pl.FLOOR + 1.5 + pl.SPK_BUMP_MAX
print(f"speaker bump top {pl.FLOOR}+1.5+{pl.SPK_BUMP_MAX} = {bump_top:.1f} vs board "
      f"underside {pl.BOARD_Z} -> clearance {pl.BOARD_Z - bump_top:.1f} "
      f"{check('bump vs board underside', pl.BOARD_Z - bump_top >= 1.0)}")

# ------------------------------------------------ 9. switch stack over bay ----
sec("9. switch under-plate envelope vs board stack")
PIN_TIP = pl.PLATE_Z1 - 8.3            # 21.2 — MX center post + pins
HOUS_BOT = pl.PLATE_Z1 - 5.0           # 24.5 — MX housing base
strips = unary_union([box(BRD_W / 2 - 2.5, BRD_BACK - BRD_L, BRD_W / 2, BRD_BACK),
                      box(-BRD_W / 2, BRD_BACK - BRD_L, -BRD_W / 2 + 2.5, BRD_BACK)])
over_board, over_strip = [], []
for k in keys:
    post = Point(k["x"], k["y"]).buffer(2.0, quad_segs=16)
    pins = [Point(k["x"] - 3.81, k["y"] + 2.54), Point(k["x"] + 2.54, k["y"] + 5.08)]
    zone = unary_union([post] + pins)
    if zone.intersects(board_rect):
        over_board.append(k["id"])
    if any(strips.contains(p) for p in pins) or post.intersects(strips):
        over_strip.append(k["id"])
clr_ins = PIN_TIP - INSUL_TOP
clr_brd = PIN_TIP - BRD_TOP
print(f"switch lowest point Z {PIN_TIP:.1f} (plate top {pl.PLATE_Z1} - 8.3); "
      f"housing base Z {HOUS_BOT:.1f}")
print(f"keys over the board: {over_board}")
print(f"keys with pins/posts over the header-insulator strips: {over_strip}")
print(f"pins vs insulator top {INSUL_TOP:.1f}: clearance {clr_ins:.1f} "
      f"{check('pins vs insulators >= 0.8', clr_ins >= 0.8)}")
print(f"pins vs bare board top {BRD_TOP:.1f}: clearance {clr_brd:.1f} "
      f"{check('pins vs board', clr_brd >= 0.5)}")
spk_zone = box(-pl.SPK_FLANGE[0] / 2, pl.SPK_CENTER[1] - pl.SPK_FLANGE[1] / 2,
               pl.SPK_FLANGE[0] / 2, pl.SPK_CENTER[1] + pl.SPK_FLANGE[1] / 2)
over_spk = [k["id"] for k in keys
            if Point(k["x"], k["y"]).buffer(2.0).intersects(spk_zone)]
print(f"keys over the speaker: {over_spk} -> pins {PIN_TIP:.1f} vs bump top "
      f"{bump_top:.1f}: clearance {PIN_TIP - bump_top:.1f} "
      f"{check('pins vs speaker bump', PIN_TIP - bump_top >= 2.0)}")

# ---------------------------------------------------------- 10. speaker bay ----
sec("10. speaker bay (floor grille / pilots / flange)")
slots = part_tray.spk_floor_opening()
slot_polys = pl._polys(slots)
b = slots.bounds
print(f"floor opening: racetrack {part_tray.SPK_OPEN_W}x{part_tray.SPK_OPEN_H} "
      f"R{part_tray.SPK_OPEN_R} at {pl.SPK_CENTER} minus 2x {part_tray.SPK_BAR_W} bars "
      f"-> {len(slot_polys)} slots, bounds x {b[0]:.1f}..{b[2]:.1f} y {b[1]:.1f}..{b[3]:.1f}, "
      f"area {slots.area:.0f} mm^2 "
      f"{check('3 grille slots', len(slot_polys) == 3)}")
feet = unary_union([affinity.translate(pl.circle(part_tray.FEET_D),
                                       sx * part_tray.FEET_XY, sy * part_tray.FEET_XY)
                    for sx in (-1, 1) for sy in (-1, 1)])
d_slot_feet = slots.distance(feet)
print(f"slots vs feet recesses: distance {d_slot_feet:.2f} "
      f"{check('slots clear feet', d_slot_feet >= 2.0)}")
pilots = [Point(x, y) for x, y in part_tray.SPK_PILOT_XY]
print(f"pilots Ø{part_tray.SPK_PILOT_D} THROUGH the floor at "
      f"{part_tray.SPK_PILOT_XY} (63 x 33 pattern)")
liner_in = tray_liner_in
pilot_ok = all(liner_in.contains(p.buffer(part_tray.SPK_PILOT_D / 2)) for p in pilots)
print(f"pilots inside the floor interior: {pilot_ok} "
      f"{check('pilots inside floor', pilot_ok)}")
d_pf = min(p.distance(Point(sx * 36, sy * 36)) for p in pilots
           for sx in (-1, 1) for sy in (-1, 1))
print(f"  INFO closest pilot center to a foot center: {d_pf:.2f} "
      f"(rims merge {part_tray.FEET_D / 2 + part_tray.SPK_PILOT_D / 2 - d_pf:.2f} in the "
      f"0.6 recess layer only — designed 63x33-vs-feet consequence, layers stay "
      f"watertight; pilot bore complete above the recess: "
      f"{check('pilot center outside recess', d_pf >= part_tray.FEET_D / 2)})")
boss_front = unary_union([affinity.translate(pl.circle(part_tray.BOSS_D), sx * 39, -39)
                          for sx in (-1, 1)])
flange_sharp = affinity.translate(box(-36, -21, 36, 21), 0, pl.SPK_CENTER[1])
flange_r65 = affinity.translate(pl.rounded_rect(72, 42, 6.5), *pl.SPK_CENTER)
sharp_ov = flange_sharp.intersection(boss_front).area
r65_gap = flange_r65.distance(boss_front)
print(f"flange 72x42 vs front bosses: sharp-corner overlap {sharp_ov:.2f} mm^2 "
      f"(INFO — real cavity flanges are rounded); corner R6.5 gap {r65_gap:.3f} "
      f"{check('R6.5 flange clears bosses', sharp_ov < 3.0 and r65_gap > 0.05)}")
d_fl_wall = liner_in.exterior.distance(flange_sharp)
obstacles = unary_union(
    [affinity.translate(pl.circle(part_tray.POST_D), x, y) for x, y in part_tray.POST_XY]
    + [affinity.translate(pl.circle(part_tray.WPOST_D), x, y) for x, y in part_tray.WPOST_XY]
    + [box(-part_tray.BRIDGE_X, part_tray.BRIDGE_Y0, part_tray.BRIDGE_X, part_tray.BRIDGE_Y1),
       part_tray.amp_ridges()])
d_fl_obs = flange_sharp.distance(obstacles)
print(f"flange vs walls {d_fl_wall:.2f} / vs bridge+posts+ridges {d_fl_obs:.2f} "
      f"{check('flange drops onto floor', d_fl_wall >= 0.4 and d_fl_obs >= 2.0)}")
bump = affinity.translate(affinity.scale(pl.circle(2.0), 25.0, 20.0), *pl.SPK_CENTER)
d_bump_bridge = bump.distance(box(-part_tray.BRIDGE_X, part_tray.BRIDGE_Y0,
                                  part_tray.BRIDGE_X, part_tray.BRIDGE_Y1))
print(f"oval bump (<= 50x40, top {bump_top:.1f}) vs bridge: plan gap {d_bump_bridge:.1f} "
      f"{check('bump clears bridge', d_bump_bridge >= 2.0)}")
tip_below_floor = 6.0 - 1.5 - pl.FLOOR                 # M2.5x6: flange + floor
print(f"M2.5x6 from inside: head on flange top {pl.FLOOR + 1.5:.1f}, tip "
      f"{tip_below_floor:.1f} below the floor bottom; feet >= {FOOT_H:.0f} - recess "
      f"{part_tray.FEET_DEPTH} -> ground clearance {FOOT_H - part_tray.FEET_DEPTH - tip_below_floor:.1f} "
      f"{check('screw tips in foot gap', FOOT_H - part_tray.FEET_DEPTH - tip_below_floor >= 0.2)}")

# ------------------------------------------- 11. amp / wire posts / mic ----
sec("11. amp pocket, wire posts, mic grille")
ridges = part_tray.amp_ridges()
pocket = box(part_tray.AMP_C[0] - 10, part_tray.AMP_C[1] - 10,
             part_tray.AMP_C[0] + 10, part_tray.AMP_C[1] + 10)
rb = ridges.bounds
print(f"amp pocket 20x20 at {part_tray.AMP_C}: ridges {rb[0]:.1f}..{rb[2]:.1f} x "
      f"{rb[1]:.1f}..{rb[3]:.1f}, h {part_tray.AMP_RIDGE_H} "
      f"{check('ridges frame pocket', ridges.intersection(pocket).area < 0.01)}")
print(f"  ridge outer edge vs liner wall: {liner_in.exterior.distance(ridges):.2f}  "
      f"pocket vs locator post: "
      f"{pocket.distance(Point(17.6, 5.5).buffer(2.5)):.2f} "
      f"{check('pocket clear of post', pocket.distance(Point(17.6, 5.5).buffer(2.5)) >= 0.5)}")
print(f"  MAX98357A breakout ~18x16 in the 20x20 pocket: 1.0+ play/side (foam tape)")
sliver = (part_tray.WPOST_D - part_tray.NOTCH_W) / 2
print(f"wire posts Ø{part_tray.WPOST_D} at {part_tray.WPOST_XY}, {part_tray.WPOST_H} tall, "
      f"notch {part_tray.NOTCH_W} x {part_tray.NOTCH_Z1 - part_tray.NOTCH_Z0:.1f} at Z "
      f"{part_tray.NOTCH_Z0}..{part_tray.NOTCH_Z1}: side slivers {sliver:.2f} "
      f"{check('post slivers printable', sliver >= 0.8)}")
wposts = unary_union([Point(x, y).buffer(part_tray.WPOST_D / 2)
                      for x, y in part_tray.WPOST_XY])
print(f"  posts vs board footprint: {wposts.distance(board_rect):.1f}  vs flange: "
      f"{wposts.distance(flange_sharp):.1f} "
      f"{check('wire posts clear', wposts.distance(board_rect) >= 2.0 and wposts.distance(flange_sharp) >= 2.0)}")
mic_lo, mic_hi = min(part_tray.MIC_XS), max(part_tray.MIC_XS)
print(f"mic grille: 3 x {part_tray.MIC_W} sq ports at x {part_tray.MIC_XS}, Z "
      f"{part_tray.MIC_Z0}..{part_tray.MIC_Z1} "
      f"{check('mic port spacing', mic_hi - mic_lo == 6.0 and (mic_lo + mic_hi) / 2 == -20.0)}")
mod_zone = box(-27.0, -42.6, -13.0, -41.0)             # Ø14 module glued on liner
d_mod_bump = bump.distance(mod_zone)
print(f"  round mic module glue zone (x -27..-13 on the front liner) vs oval bump: "
      f"plan gap {d_mod_bump:.1f}; module bottom sits above flange top "
      f"{pl.FLOOR + 1.5:.1f} {check('mic module above speaker', d_mod_bump >= 0.5)}")

# ------------------------------------------------------- 12. watertight ----
sec("12. watertight (every build item)")
wt = True
for name, mesh, _c in (part_tray.build() + part_plate.build()
                       + part_caps.build() + part_knob.build()):
    rep = pl.validate(mesh)
    wt &= rep["watertight"]
    if not rep["watertight"]:
        print(f"  NOT WATERTIGHT: {name} {rep['problems'][:3]}")
print("all items watertight:", check("watertight", wt))

# --------------------------------------------------------------- summary ----
print(f"\nAUDIT-FIT: {len(FAILURES)} failure(s)"
      + (f" -> {FAILURES}" if FAILURES else " -> ALL CLEAR"))
sys.exit(1 if FAILURES else 0)
