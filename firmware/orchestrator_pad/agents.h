#pragma once
#include <Arduino.h>
#include "config.h"

// What each key does. EDIT this grid to match how your keycaps are laid out.
// One key is the mic (hold-to-talk); the agent keys select/lock that agent in
// Loom. Each agent gets a status-LED colour so you can see who's selected.
enum KeyRole { ROLE_NONE, ROLE_MIC, ROLE_AGENT };

struct KeyBind {
  KeyRole     role;
  const char *agent;      // Loom agent id, for ROLE_AGENT
  uint8_t     r, g, b;    // status-LED colour when selected
};

// Layout mirrors matrix.h. K1 is the mic (row0/col0 — matches TALK_ROW/COL).
// K2..K7 are the six Loom agents; the rest are spare for now.
static const KeyBind KEYMAP[MATRIX_ROWS][MATRIX_COLS] = {
  // C0 (G14)                       C1 (G8)                            C2 (G17)                          C3 (G18)
  {{ROLE_MIC,   nullptr,      60,0,0}, {ROLE_AGENT,"claude-code", 70,35,0}, {ROLE_AGENT,"opencode",  0,45,45}, {ROLE_NONE, nullptr, 0,0,0}}, // R0: K1 mic · K2 · K3 · (dial hole)
  {{ROLE_AGENT,"codex",       0,50,0}, {ROLE_AGENT,"grok-code",  45,45,45}, {ROLE_AGENT,"antigravity",15,20,70}, {ROLE_AGENT,"kiro", 45,0,70}}, // R1: K4 · K5 · K6 · K7
  {{ROLE_NONE,  nullptr,      0,0,0},  {ROLE_NONE, nullptr,       0,0,0},   {ROLE_NONE, nullptr,      0,0,0},   {ROLE_NONE, nullptr, 0,0,0}}, // R2: K8..K11 spare
  {{ROLE_NONE,  nullptr,      0,0,0},  {ROLE_NONE, nullptr,       0,0,0},   {ROLE_NONE, nullptr,      0,0,0},   {ROLE_NONE, nullptr, 0,0,0}}, // R3: K12..K14 spare
};

inline const KeyBind &keyAt(uint8_t r, uint8_t c) { return KEYMAP[r][c]; }
