# Orchestrator Pad — voice backend

The little server the pad talks to. It runs on your Mac (the same machine as
the Loom daemon, reachable over your LAN or tailnet) and turns a held-to-talk
recording into a spoken answer:

```
pad mic ──16 kHz PCM──▶  /voice  ──▶  STT  ──▶  brain  ──▶  TTS  ──▶  16 kHz PCM ──▶ pad amp
                                    (Groq/DG)   (Loom│LLM)  (Deepgram)
```

Everything speaks **one audio format end to end — 16 kHz, 16-bit, mono PCM** —
so there's no transcoding anywhere: the mic records it, Deepgram is asked to
return it, and the amp plays it straight off the wire.

Zero npm dependencies — just Node's built-in `http`, `fetch`, and `FormData`.
Node ≥ 20.

## Setup

```bash
cd backend
cp .env.example .env      # then fill in the two keys
npm start
```

You need **two API keys** in `.env` (it's gitignored — keys never get committed):

| Key | Used for | Get it |
|---|---|---|
| `GROQ_API_KEY` | LLM (`llama-3.3-70b`), and STT if you enable Groq whisper | <https://console.groq.com/keys> |
| `DEEPGRAM_API_KEY` | TTS (`aura-2-thalia`), and STT by default (`nova-2`) | <https://console.deepgram.com/> |

On start it fails loud if either key is missing. Everything else has a sane
default (see `.env.example`), so a fresh clone runs with just those two set.

### STT provider

Speech-to-text is Deepgram `nova-2` out of the box. Groq's whisper is faster
but Groq gates audio models per-project — once you've enabled them for your
key's project, set `STT_PROVIDER=groq` and STT moves to Groq whisper. The LLM
is always Groq; TTS is always Deepgram.

## The brain: Loom vs. LLM

- **`loom`** (default when the daemon is reachable): the pad drives Loom.
  Selecting an agent is a **handoff** — it locks that agent and shows up in the
  thread. A held-to-talk turn is posted as a **message** to that agent; the
  backend polls the daemon's events and speaks the agent's reply. Real work
  takes a while, so if the agent is still going after `LOOM_REPLY_TIMEOUT_MS`
  the pad hears "sent — check the thread" instead of hanging.
- **`llm`**: a standalone Groq chat, no Loom. Good for a desk toy or when the
  daemon isn't running. The pipeline is otherwise identical.

It auto-detects at startup: if `LOOM_URL` (default `http://127.0.0.1:7420`)
answers, it uses Loom; otherwise it falls back to the LLM. Force it with
`BRAIN=loom` or `BRAIN=llm`.

When the backend runs on the same machine as the daemon it bootstraps the
admin token over loopback — **no token to configure**. Set `LOOM_TOKEN` only
for a remote daemon over the tailnet.

## Endpoints

| Method + path | Body | Returns |
|---|---|---|
| `GET /health` | — | JSON: `brain`, selected `agent`, `agents`, `models` |
| `POST /select` | `{"agent":"claude-code"}` | locks the agent in Loom (a handoff) |
| `POST /voice?agent=…` | raw PCM (16 kHz/16-bit/mono) | PCM reply body + `X-Transcript` / `X-Reply` / `X-Agent` headers |
| `GET /speak?text=…` | — | PCM of the spoken text (the "connected" cue, telnet `say`) |

`/voice` and `/speak` return the reply with a **`Content-Length`** (not chunked)
on purpose: the ESP32 reads the raw body stream, and chunk markers would
corrupt the PCM.

## Tests

```bash
npm test            # unit + integration + loom  (12 tests)
npm run test:unit   # WAV framing, isWav, config  — no network
npm run test:voice  # audible end-to-end on macOS (uses `say` + `afplay`)
```

- **unit** — `pcmToWav` header bytes, `isWav` boundaries, config loading.
- **integration** — spawns the server with `BRAIN=llm`, synthesizes a real
  16 kHz WAV with macOS `say`, POSTs it to `/voice`, and asserts the round trip
  (e.g. "what's the capital of France" → a reply containing "Paris").
- **loom** — skips gracefully when no daemon is up.

`npm run test:voice` is the fun one: it speaks a prompt, sends it, and plays the
answer out loud — the whole pipeline without the hardware.

## Pointing the pad at it

The pad asks for your Mac's address in its setup portal. Find it:

```bash
ipconfig getifaddr en0      # LAN (Wi-Fi)
tailscale ip -4             # tailnet, if you use Tailscale
```

Enter that IP and port `8080` in the "LoomPad-Setup" portal (see
[`../firmware`](../firmware)). The server binds `0.0.0.0` so anything on your
LAN/tailnet can reach it.

## Files

| File | What |
|---|---|
| `server.mjs` | HTTP server + the routes above; `think()` picks Loom vs. LLM |
| `providers.mjs` | `stt()`, `llm()`, `ttsStream()`, WAV framing |
| `loom.mjs` | daemon bridge: bootstrap token, handoff, message, poll for reply |
| `config.mjs` | all config from env, with a tiny dependency-free `.env` loader |
| `test/` | unit · integration · loom |
| `test-voice.mjs` | audible end-to-end harness |
