# Orchestrator Pad — dimensional spec (v6)

Open-source ESP32 macropad for orchestrating coding agents: lock a target agent
(Grok / Codex / Claude Code / Antigravity / opencode / Kiro / Cursor),
hold-to-talk voice capture, and a dial that sets model effort
(`low → medium → high → xhigh → max → ultracode`).

All dimensions in **mm**. Axes: X right, Y back (away from user), Z up.
Origin: center of the case footprint, Z=0 at the tray's outer bottom face.

## Layout (19.05 mm grid, 4 columns x 4 rows)

Column centers X: -28.575, -9.525, +9.525, +28.575 (cols 0..3)
Row centers Y: +28.575, +9.525, -9.525, -28.575 (rows 0..3, row 0 = back/top)

| Pos | What | Glyph (debossed) |
|---|---|---|
| r0c0 | EC11 rotary encoder (effort dial) | knurled knob, tick dot |
| r0c1 | agent key: Cursor | `cursor` (cube, raised facet) |
| r0c2 | agent key: Codex | `codex` (cloud, raised `>_`) |
| r0c3 | preset/status key (translucent look) | `target` |
| r1c0..c3 | agent keys: Grok, Claude Code, Antigravity, opencode | `grok` (circle-slash), `claude` (pixel-pal), `antigravity` (arch), `opencode` (frame) |
| r2c0 | agent key: Kiro | `kiro` (ghost) |
| r2c1..c3 | run / approve / reject | `bolt`, `check`, `cross` |
| r3c0 | prompt/terminal key | `prompt` |
| r3 c1–c2 | **voice bar, 2u** (hold-to-talk), centered at X=0 | `mic` |
| r3c3 | send/dispatch key | `send` |

Total: **14 MX switches** (13 x 1u + 1 x 2u), 1 EC11 encoder.

## Case (two printed shells + knob + caps)

### Tray (bottom shell) — `part_tray.py`
- Outer: 90.0 x 90.0, corner R8, height **28.0** (fat base — the interior is
  a component bay). Wall 2.4, floor 2.4.
- Ledge for the top's skirt: below Z=21.5 wall is 2.4 thick; above Z=21.5 the
  inner face steps out so wall is **1.2** thick (skirt seat).
- 4 corner bosses Ø7.0 at (±39, ±39): solid pedestal from floor top (Z2.4)
  to **Z=19.5**, insert ring Ø7.0/Ø4.0 to **Z=25.5** (bore 6.0 deep from the
  top, floor at Z 19.5 — M3 heat-set insert).
- **USB windows**, BOTH side walls (X=+45 and X=-45): each **26.0 wide** in
  Y centered Y=0, **Z 17.0..23.5**, through BOTH wall columns. v6 turns the
  board 90° so its ports face a side wall, and the bay is **reversible** —
  the board installs **ports-right or ports-left**, and the *unused* window
  is documented as a **wire pass-through** (run the speaker/mic/amp harness
  or a USB extension out of it). The board's dual side-by-side USB-C ports
  sit on its TOP face (shells 8.94 x 3.3 → Z 17.6..20.9, center 19.25) and
  exit through whichever window they face; each window is wide + tall enough
  that exact port offsets don't matter (shells stay inside for port centers
  |y| ≤ 8.53, a 12-wide plug hood for |y| ≤ 7.0), and the receptacle face
  sits only ~1.7 behind the outer wall — under the ~2.5 of exposed plug
  shroud, so any hood works at the aperture mouth. Each window top crosses
  the 21.5 ledge; the plate skirt is notched over both. The two side cuts
  split each cut wall band into a back arc and a front arc — every piece is
  still its own watertight prism, fused to the solid ring bands above and
  below by the 0.2 lap.
- **Board bay (rotated + REVERSIBLE)** — dual-USB-C ESP32-S3 clone,
  components UP, factory header pins DOWN, laid **along X**: up to **64.0
  long (X) x 30.0 wide (Y)**, centered Y=0 (|y| ≤ 15). Two installs, both
  seating identically because every bay feature is mirror-symmetric about
  X=0:
  - **ports-right** X **-22.0 … +42.0** (USB-C exits the X=+45 window)
  - **ports-left**  X **-42.0 … +22.0** (USB-C exits the X=-45 window)
  - side shelves (BOTH walls): tabs protruding 1.6 from each side wall's
    inner face (42.6), spanning **|x| 41.0..42.8** (0.2 lap into the liner)
    and **|y| ≤ 14.0**, body Z 13.5..16.0 — the board's port edge seats on
    one and its far edge overhangs the other; **Z=16.0** top faces (1.0
    bearing, 0.6 edge-to-wall gap on the port side).
  - mid-span ribs: two walls at **X +4.0..+7.0** and **X -7.0..-4.0**,
    **Y +1.0..+16.0**, floor to **Z=16.0** — they carry the board's middle
    (~112 mm² of total seat bearing per orientation). They stay at Y ≥ +1.0
    on purpose: the speaker flange occupies X ±36, Y -42..0, and a rib
    crossing it would foul the flange (1.0 clear as drawn).
  - 4 locator posts Ø5.0, tops **Z=19.0**, at **(±20.0, +17.6)** and
    **(±39.0, -17.6)**: lateral cage in Y only, inner faces at |y| = 15.1 →
    0.1 clearance per side to a 30-wide board, 1.4 above the board top.
    Each orientation is caged by three of the four (two north, one south);
    the Y-negative pair sits at |x| = 39 so it clears the speaker flange
    edge at 36 by 0.5.
  - under-board clearance floor→16.0 = **13.6 mm** for the soldered header
    pins (~8.5 under the PCB) + angled dupont connectors. Headers now run
    along the board's long edges (y = ±15). Wire in the open pockets either
    side of the ribs. Pin tails that land over a rib (X ±4..7, Y +1..+16)
    must be clipped flush; over the speaker zone (Y < 0) the driver bump can
    rise to Z 14.9 under the pin rows — clip there too, or verify your
    speaker's bump footprint. (Headers usually stop ~2 mm short of the
    board ends, clearing the 1.0 shelf lip.)
- **Speaker bay** (down-firing, flange ON the floor, centered (0, -21)):
  - floor opening: racetrack (rounded-rect R12) **54 x 24** at (0, -21) with
    two 2.0-wide grille bars along X → 3 slots (~6.7 each), through both
    floor layers.
  - 4 screw pilots Ø2.4 THROUGH the floor at (±31.5, -37.5) and
    (±31.5, -4.5) — the 63 x 33 pattern. M2.5 x 6 self-tappers from inside:
    heads on the flange, tips end 2.1 under the floor, inside the ≥3 mm
    foot gap. The two back pilots' bottom rims merge ~1.0 into the front
    feet-recess rims (0.6 recess layer only) — stick those feet biased
    outward.
  - fits flanges up to **72 x 42** (a sharp-cornered 72 x 42 grazes the two
    front bosses by ~0.5; real cavity flanges with corner R ≥ 6.5 clear —
    **measure yours**) and driver bumps up to **Ø50 x 11 tall** (oval, ≤
    50 x 40 in plan): bump top 2.4 + 1.5 + 11 = **14.9** clears the board
    underside at 16.0 by 1.1. **Measure the bump height — the bay assumes
    ≤ 11.**
- **Amp pocket**: four L-corner ridges (1.5 wide, 2.0 tall, 6-long legs)
  framing a 20 x 20 pocket centered **(+22, +27)** — the MAX98357A drops in,
  foam-tape mounted. v6 moved it to the back strip, out from under the
  rotated board: the ridges span X 10.5..33.5, Y 15.5..38.5, so the outer
  edge clears the board edge at Y 15.0 by **0.5** (both orientations), the
  corner bosses' inner face at X 35.5 by **2.0**, and the speaker by 15.5.
  The (+20, +17.6) locator post clips the nominal pocket's south edge (it
  rises to Y 20.1); the **post-free rectangle is still 20 x 16.9** (Y
  20.1..37), so an ~18 x 16 breakout drops in biased north.
- **Wire posts**: two Ø5.0 posts, 8.0 tall, at **(-30, +20)** and
  **(-30, +34)**, each with a 3.2-wide x 2.0-tall through-notch at Z 3..5
  for zip ties (west wiring channel). v6 pushed them north-east so they sit
  out from under the rotated board (2.5 clear of the ports-left footprint)
  and out of the left window corridor (9.7 clear of the y ±13 aperture),
  while still clearing the (-39, +39) corner boss by 4.3.
- **Mic grille**, front wall (Y=-45): 3 x 1.5 square ports, spacing 3.0,
  centered X=-20, **Z 19.4..20.9** — fully below the 21.5 ledge; the round
  I2S mic module glues behind them, above the speaker body. (Replaces v3's
  low-Z round ports.)
- Feet recesses: bottom face, 4 x Ø9.0 x 0.6 deep at (±36, ±36). Use
  **≥3 mm tall feet** so the down-firing speaker breathes (and the M2.5
  tips stay 0.3 off the desk).

### Top plate — `part_plate.py`
- Plate: 90.0 x 90.0, R8, **1.5 thick**, spans Z 28.0 → 29.5 (counterbore
  bands 28.0..28.7 + 28.5..29.5; case stack ~29.5 mm + caps/knob).
- 14 MX cutouts **14.1 x 14.1** (14.0 nominal + 0.1 print tolerance) at the
  grid positions above (2u voice = one switch centered at X=0, r3). These
  are exactly donor-keyboard-style plate holes — harvested 3-pin white MX
  clones clip straight into the 1.5 plate.
- **Switch sockets + deck (v5.1, donor-board style, print-clean)**: under
  every cutout a pocket box cages the switch body — walls 1.6 (outer 17.3
  sq) from **Z 24.5** (the MX base-seat plane, plate top − 5.0) up 0.2 into
  the plate. Flipped for printing, the plate is pure vertical walls: no
  bridges, no floating regions, no supports. The footprint floor is the
  separate **switch deck**: a 1.2-thick flat sheet (78 × 78 R6, Z
  23.3..24.5) carrying all 14 MX clusters — center post Ø**4.15** (snug on
  the Ø4.0 post), contact pin holes Ø**2.0** at (−3.81, +2.54) and
  (+2.54, +5.08), 5-pin leg holes Ø**1.85** (snug on Ø1.7) at (±5.08, 0);
  offsets from each key center, +Y toward the back. It prints FLAT
  (perfect holes), presses onto the switch posts/legs from below
  (friction-fit), seats against the socket-wall rims, has a 16 sq cutout
  under the EC11 body and Ø8.8 notches at the four screw towers (≥0.15,
  audited). The metal pins protrude **2.1** below the deck (tips Z 21.2):
  solder the matrix wires directly to them, PCB-style.
- Knob hole Ø**7.4** at r0c0 (EC11 M7 threaded bush).
- Skirt: ring 1.15 thick x 6.7 deep (Z 21.5 → 28.2), outer profile =
  87.3 x 87.3 R6.9 x-y, inner 85.0 x 85.0 R6.3 (drops inside the tray's
  87.6 upper 1.2 wall with ~0.15 clearance per side). Notched so the case
  closes and USB mates: **Ø8.6 corner clearances** at (±39, ±39) around the
  tray bosses (which rise to Z 25.5, through the skirt band), plus **TWO
  side notches** spanning **y -14..+14** (full skirt depth) at
  **x +41..+44** and **x -44..-41** — each tray USB window top (23.5)
  crosses the 21.5 ledge, so the notches open both window corridors for the
  aperture and the plug hood, whichever side the ports face (1.0 margin per
  side over the y ±13 aperture). The ring survives as 6 segments (4 boss
  cuts + 2 side notches), each a watertight prism fused to plate band A.
  (v3's separate USB/UART and front mic notches are gone: the mic grille
  sits below the ledge.)
- 4 screw towers Ø7.6 from Z 25.5 → 28.2 at (±39, ±39), through-hole Ø3.4
  continuing through the plate, counterbore Ø6.4 x 0.8 from the top face
  (M3 x 8 button-head into the tray inserts).

### Keycaps — `part_caps.py`
- 1u: base 18.2 x 18.2 R2.5, top 16.4 x 16.4 R2.2, height **7.5** (loft taper),
  wall 1.6, hollow underneath.
- 2u voice bar: base 37.25 x 18.2, top 35.4 x 16.4, same height/wall.
- MX stem: post Ø5.8, length 3.9 below the cap ceiling; cross slots
  4.15 x 1.35, depth 3.9 (friction fit on MX stem).
- Glyphs debossed **0.6** into the top: build the top 0.8 mm of the cap as a
  layer with glyph-shaped holes; solid body below ends 0.6 lower, glyph
  islands (e.g. the pixel-pal's eyes) overlap 0.2 into the body below so every
  shell fuses when sliced.
- **Legend infills**: each glyph also exports as a separate flush 0.6 prism
  (`<id>-legend` items, merged into `exports/legends-all.stl`, same drop as
  `caps-all.stl` so both stay aligned). Print caps + legends together in two
  colors (AMS/MMU, or a manual filament swap on the last 3 layers when caps
  print top-face-down), or skip the file and paint-fill the recesses. Legend
  colors per key live in `partlib.key_layout()` (white on colored caps, dark
  gray on white caps).

### Knob — `part_knob.py`
- Ø17.0, height 15.0. Knurl: 24 flutes (Ø1.6 scallops on the rim).
- Top: 1.5 chamfer loft to Ø16.0, tick-dot deboss near edge.
- Nut recess: **Ø12.6 x 2.4** counterbore in the bottom face, concentric with
  the bore — swallows the EC11 M7 panel nut (~Ø11.5 across corners x 2.2)
  sitting on the plate.
- Bore: EC11 D-shaft — Ø6.1 with flat at 4.6, blind, above the recess to
  z 12.0 (3.0 ceiling).

## Assembly (`assembly.py`)
- Tray at Z0 → plate on top (plate top face Z=29.5).
- Caps: bottom face at **Z=35.0** (switch seated, cap floats ~5.5 over plate).
- Knob: bottom at **Z=30.5** over r0c0 (M7 nut hidden in the recess).
- Exports: `exports/orchestrator-pad-assembled.glb`, `exports/orchestrator-pad-exploded.glb`
  (tray +0 / plate +20 / caps +40 / knob +52), plus one STL per printable part
  (`tray`, `plate`, `caps-all`, `legends-all`, `knob`).

## Colors (GLB preview only)
tray `#AEB4BC`, plate `#F4F5F7`, preset cap `#D8DCE2`, Grok `#141414`,
Codex `#6366F1`, Claude Code `#D97757`, Antigravity `#2D6BFF`,
opencode `#FAFAF8`, Kiro `#7A3FF2`, Cursor `#26282E`,
run/approve/reject/prompt/send `#FFFFFF`, voice bar `#FFFFFF`, knob `#E8E9EB`.
Legends: white `#FFFFFF` on colored caps, dark `#3F444D` on white caps,
mid `#8A919E` on the preset.

Logo glyphs (`grok`, `codex`, `claude`, `antigravity`, `opencode`, `kiro`,
`cursor`) are simplified geometric homages debossed 0.6 into the caps; the
original marks belong to their respective projects.

## BOM (v6)
Dual-USB-C ESP32-S3 clone board **with factory pin headers** (pins DOWN,
components + USB-C on TOP — the 13.6 under-board bay swallows the ~8.5 pin
tails; v3's headerless rule is gone). **Fit it sideways**: the board lies
along X with its ports facing a side wall, and you choose **ports-right or
ports-left** at assembly time — the bay is symmetric, so both drop in the
same way. Also: MAX98357A I2S amp breakout, 4Ω 3W
cavity speaker (flange ≤ 72 x 42, driver bump ≤ 11 tall — **measure it**)
+ 4 x **M2.5x6** self-tappers, round I2S mic module (INMP441-class), EC11
encoder (M7 bush) + this knob, 14 x MX-style switches (donor-harvested
3-pin white MX clones fine), 4 x M3 heat-set inserts + **M3x8** button-head
screws (an M3x10 bottoms out in the Ø4.0 x 6.0 boss bore 0.8 before the
head clamps — head bears at Z 28.7 under the counterbore), 4 x rubber feet
Ø8 **≥3 mm tall** (down-firing speaker + screw-tip clearance), zip ties
for the wire posts, jumper wires. Optional: WS2812 under the preset keys.

## Print notes
0.4 nozzle, 0.2 layers, PETG or PLA. Tray + plate flat side down, no
supports (the **two** 26 mm bridges over the side USB windows and the
**two** 1.6 shelf tabs print unsupported; the mid-span ribs are plain
3.0-thick walls off the floor). Caps upside down (top face on bed) or with
tree supports;
knob upright. Case is ~29.5 tall; with caps ≈ 42.5 overall (knob crown at
45.5). Every part = union of closed shells; slicers merge
coplanar/overlapping shells.
