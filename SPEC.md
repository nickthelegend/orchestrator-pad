# Orchestrator Pad — dimensional spec (v4)

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
- **USB window**, back wall (Y=+45): **26.0 wide** centered X=0,
  **Z 17.0..23.5**, through BOTH wall columns. The board's dual side-by-side
  USB-C ports sit on its TOP face (shells 8.94 x 3.3 → Z 17.6..20.9, center
  19.25) and exit here; the window is wide + tall enough that exact port
  offsets don't matter (shells stay inside for port centers |x| ≤ 8.5, a
  12-wide plug hood for |x| ≤ 7.0), and the receptacle face sits only ~1.7
  behind the outer wall — under the ~2.5 of exposed plug shroud, so any
  hood works at the aperture mouth. The window top crosses the 21.5 ledge;
  the plate skirt is notched over it. (Replaces v3's X=+7.79 slot and the
  UART relief pocket.)
- **Board bay** — dual-USB-C ESP32-S3 clone, components UP, factory header
  pins DOWN, centered X=0, back edge at Y=+42.0, up to **30.0 wide x 64.0
  long**:
  - back shelf: tab protruding 1.6 from the back-wall inner face, x -14..14,
    body Z 13.5..16.0 — the board's back edge seats on its **Z=16.0** top
    face (1.0 bearing, 0.6 edge-to-wall gap).
  - front bridge: wall x -16..16, Y +4.0..+7.0, floor to **Z=16.0** —
    mid-span support between the speaker bay and the wiring bay.
  - 4 locator posts Ø5.0, tops **Z=19.0**, at (±17.6, 40.0) and
    (±17.6, +5.5): lateral cage only, 0.1 clearance per side to a 30-wide
    board, 1.4 above the board top.
  - under-board clearance floor→16.0 = **13.6 mm** for the soldered header
    pins (~8.5 under the PCB) + angled dupont connectors. Wire in the open
    bay **Y +7..+41**. Pin tails that land over the bridge (Y +4..+7) must
    be clipped flush; over the speaker zone (Y < +4) the driver bump can
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
  framing a 20 x 20 pocket centered (+31, +14) — the MAX98357A drops in,
  foam-tape mounted.
- **Wire posts**: two Ø5.0 posts, 8.0 tall, at (-34, +12) and (-34, +30),
  each with a 3.2-wide x 2.0-tall through-notch at Z 3..5 for zip ties
  (west wiring channel).
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
- **Switch sockets (v5, donor-board style)**: under every cutout, a pocket
  box cages the switch body — walls 1.6 (outer 17.3 sq) from Z 23.3 up 0.2
  into the plate, and a **1.2 socket floor** whose top sits at **Z 24.5**
  (= plate top − 5.0, the MX shoulder→base depth) so the base seats fully
  while the clips engage the plate. The floor carries the MX footprint:
  center post Ø4.3 at (0,0), contact pin holes **Ø2.8** at (−3.81, +2.54)
  and (+2.54, +5.08), 5-pin leg holes Ø2.0 at (±5.08, 0) — offsets from
  each key center, +Y toward the back. The two metal pins protrude **2.1**
  below the floor (tips Z 21.2): solder the matrix wires directly to them,
  PCB-style. The three corner-adjacent sockets are notched by a Ø8.8
  keep-out around the screw towers (≥0.15 clearance, audited).
- Knob hole Ø**7.4** at r0c0 (EC11 M7 threaded bush).
- Skirt: ring 1.15 thick x 6.7 deep (Z 21.5 → 28.2), outer profile =
  87.3 x 87.3 R6.9 x-y, inner 85.0 x 85.0 R6.3 (drops inside the tray's
  87.6 upper 1.2 wall with ~0.15 clearance per side). Notched so the case
  closes and USB mates: **Ø8.6 corner clearances** at (±39, ±39) around the
  tray bosses (which rise to Z 25.5, through the skirt band), plus ONE back
  notch spanning **x -14..+14** (full skirt depth) — the tray's USB window
  top (23.5) crosses the 21.5 ledge, so the notch opens the whole window
  corridor for the aperture and the plug hood. (v3's separate USB/UART and
  front mic notches are gone: the v4 mic grille sits below the ledge.)
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

## BOM (v4)
Dual-USB-C ESP32-S3 clone board **with factory pin headers** (pins DOWN,
components + USB-C on TOP — the 13.6 under-board bay swallows the ~8.5 pin
tails; v3's headerless rule is gone), MAX98357A I2S amp breakout, 4Ω 3W
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
supports (the 26 mm bridge over the USB window and the 1.6 shelf tab print
unsupported). Caps upside down (top face on bed) or with tree supports;
knob upright. Case is ~29.5 tall; with caps ≈ 42.5 overall (knob crown at
45.5). Every part = union of closed shells; slicers merge
coplanar/overlapping shells.
