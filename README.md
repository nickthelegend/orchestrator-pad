<div align="center">

<img src="docs/images/hero.png" alt="Orchestrator Pad — 3D-printed macropad with agent keys, voice bar and effort dial" width="760">

# Orchestrator Pad

**A desk controller for your coding agents.**
Lock an agent with one key. Hold the bar and talk. Twist the dial to set how hard the model thinks.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![MCU](https://img.shields.io/badge/MCU-ESP32--S3-e7352c.svg)](https://www.espressif.com/en/products/devkits)
[![Printable](https://img.shields.io/badge/3D%20print-FDM%2C%20no%20supports-8a2be2.svg)](#print-it)
[![CAD](https://img.shields.io/badge/CAD-numpy%20%2B%20shapely-013243.svg)](#the-cad-is-code)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-19b36b.svg)](#roadmap)

[Print it](#print-it) · [What's inside](#whats-inside) · [How a job flows](#how-a-job-flows) · [The CAD is code](#the-cad-is-code) · [Roadmap](#roadmap)

</div>

---

Pointing five different CLI agents at your projects means five terminals and a
lot of retyping. The Orchestrator Pad is a small (~90 × 90 mm) open-source
macropad that turns the routing into muscle memory: **one key per agent, one
bar for your voice, one dial for effort** — from `low` all the way up to
`ultracode`. It speaks Wi-Fi to your orchestrator daemon, with USB-HID as the
fallback.

Everything here is remixable: the enclosure is parametric Python, the agents
on the caps are just a table in `cad/partlib.py`, and the whole thing prints
on a bed-slinger in an evening.

## The deck

<div align="center">
<img src="docs/images/top.png" alt="Top view — key layout" width="520">
</div>

| | Key | Cap | What it does |
|---|---|---|---|
| 🎛 | **Effort dial** | knurled knob | detents map to `low → medium → high → xhigh → max → ultracode` |
| ⬜ | **Cursor** | cube-facet logo | lock jobs to Cursor |
| 🟣 | **Codex** | cloud `>_` logo | lock jobs to Codex |
| ⚪ | Preset | `◎` | saved context / status (RGB glow optional) |
| ⬛ | **Grok** | circle-slash logo | lock jobs to Grok |
| 🟧 | **Claude Code** | pixel-pal logo | lock jobs to Claude |
| 🟦 | **Antigravity** | arch logo | lock jobs to Antigravity |
| ⬜ | **opencode** | terminal-frame logo | lock jobs to OpenCode |
| 🟪 | **Kiro** | ghost logo | lock jobs to Kiro |

Every glyph is debossed 0.6 mm **and** ships with a matching legend infill
piece, so the logos print in a contrast color (white on the colored caps,
charcoal on the white ones) — no more squinting.
| ⚡ | Run | `⚡` | kick off the queued job |
| ✓ | Approve | `✓` | accept a plan / permission prompt |
| ✕ | Reject | `✕` | decline / cancel |
| ⟩_ | Prompt | `⟩_` | focus the target session's terminal |
| 🎤 | **Voice bar (2u)** | `🎤` | **hold to talk** — audio streams to the daemon for speech-to-text |
| ➤ | Send | `➤` | dispatch to the locked agent at the dialed effort |

## How a job flows

```
hold 🎤 ──► ESP32-S3 streams mic audio ──► daemon does STT
release ──► { agent: "claude", effort: "ultracode", prompt: "..." }
press ➤ ──► daemon routes the job to the locked agent's session
   ✓ / ✕ ──► answer the agent's next approval prompt from the pad
```

The pad itself stays dumb on purpose: it emits a tiny JSON protocol
(`{agent, action, effort, audio?}`) over WebSocket and lets the daemon own
speech-to-text, session routing, and CLI orchestration. Point it at your own
stack by implementing one message handler.

## Print it

<div align="center">
<img src="docs/images/parts.png" alt="Printable parts — tray, plate, keycaps, knob" width="900">
</div>

| Part | File | Orientation | Supports |
|---|---|---|---|
| Tray (bottom) | [`exports/tray.stl`](exports/tray.stl) | as exported, flat on bed | none |
| Plate (top) | [`exports/plate.stl`](exports/plate.stl) | **flip 180°** — top face on bed | none |
| Keycaps ×14 | [`exports/caps-all.stl`](exports/caps-all.stl) | **flip 180°** — cap tops on bed | none |
| Legend infills ×14 | [`exports/legends-all.stl`](exports/legends-all.stl) | import **with** caps-all, flip together | none |
| Dial knob | [`exports/knob.stl`](exports/knob.stl) | upright | none |

0.4 mm nozzle · 0.2 mm layers · PETG or PLA. Slow the first layer and outer
walls for crisp glyphs. Each STL is a union of individually watertight
shells — every mainstream slicer merges them automatically.

**Two-color legends:** import `caps-all` + `legends-all` in one plate (they're
pre-aligned), flip 180° together, and assign the legend object a contrast
filament (AMS/MMU). Flipped, the legends are the **first 3 layers on the
bed**, so even a single-extruder printer can do it with one manual filament
swap at layer 4. No multi-color setup? Print caps alone and paint-fill the
recesses — they're 0.6 mm deep on purpose.

Tolerances assume a reasonably tuned printer; every clearance is a named
constant in [`SPEC.md`](SPEC.md) if yours runs tight.

## What's inside

<div align="center">
<img src="docs/images/exploded.png" alt="Exploded view" width="700">
</div>

| Qty | Part | Notes |
|---|---|---|
| 1 | **ESP32-S3 DevKitC-1** | *without* factory pin headers (or clip them flush) — it drops between the tray rails onto support pads, native USB port lines up with the case slot |
| 14 | MX-style switches | 13 × 1u + 1 for the 2u voice bar; hand-wired 4×4 matrix |
| 1 | EC11 rotary encoder | M7 bush mounts in the plate; 15 mm D-shaft; the knob hides the nut |
| 1 | INMP441 I2S microphone | sits behind the front mic grille |
| 4 | M3 heat-set inserts + **M3×8** button-head screws | tray bosses ← plate counterbores |
| 4 | rubber feet Ø8 | recessed pockets underneath |
| — | optional: WS2812 LEDs | under the three preset keys |

Assembly: heat-set the four inserts, drop the DevKitC between the rails
(USB-C into the back slot), clip the switches into the plate, hand-wire the
matrix, glue the mic behind the grille, screw the sandwich together, press on
caps and knob. A strip of kapton over the module can is cheap insurance under
the switch pins.

## The CAD is code

No STEP files, no Fusion — the entire enclosure is generated by
[`cad/partlib.py`](cad/partlib.py), a ~500-line kernel that extrudes 2D
`shapely` profiles into watertight shells (**zero 3D CSG**, so there's nothing
to corrupt), plus one script per part. Change a constant, rerun, reprint:

```bash
python3 -m venv .venv && .venv/bin/pip install numpy shapely
cd cad
../.venv/bin/python assembly.py      # STLs + GLBs + MANIFEST.json
../.venv/bin/python render_docs.py   # re-render the README images (numpy only)
```

<details>
<summary><b>Design notes & receipts</b></summary>

- Every part is validated for closed, manifold, positive-volume shells on
  every build (`partlib.validate`) — the manifest records the results.
- The fit audits in `cad/audit_*.py` are re-runnable: they check switch
  cutouts, screw stacks, cap clearances, and the DevKitC seating against
  **Espressif's official board drawing** — which is how we caught that the
  DevKitC-1's USB ports sit 7.79 mm off the board centerline. The case slot
  is centered on the *native/OTG* port, not the board.
- Keycaps use a hollow tapered loft with a printed MX cross stem and 0.6 mm
  debossed glyphs built as layered shells — no boolean subtraction anywhere.
- `exports/orchestrator-pad-assembled.glb` and `-exploded.glb` are the full
  colored models — drop them into any glTF viewer.

</details>

## Roadmap

- [x] v1 printable enclosure, caps, knob — parametric CAD + audited fit (branch [`v1`](../../tree/v1))
- [x] v2 logo keycaps (Grok · Codex · Claude Code · Antigravity · opencode · Kiro · Cursor), two-color legend infills, taller case for full DevKitC clearance, USB mating relief
- [ ] `firmware/` — ESP-IDF: matrix scan, encoder detents, hold-to-talk ring
      buffer, WebSocket client, USB-HID fallback
- [ ] daemon reference handler + pairing flow
- [ ] hand-wire guide with photos
- [ ] PCB with hotswap sockets + WS2812
- [ ] translucent-PETG preset keys with light pipes

PRs welcome — the fastest way to help is to print one and file issues with
your tolerance notes.

## License

[MIT](LICENSE). The agent names and logo-inspired cap glyphs refer to
third-party projects — the marks belong to their respective owners; the
glyphs here are simplified geometric homages for personal builds.
