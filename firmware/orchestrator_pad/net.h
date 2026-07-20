#pragma once
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "config.h"
#include "settings.h"
#include "audio.h"

// Talks to the backend (the tailnet server on the Mac). The backend does STT →
// Loom/LLM → TTS and hands back raw 16 kHz PCM with a Content-Length, which we
// stream straight to the amp as it downloads.
class Net {
public:
  void begin(Settings *s) { _s = s; }
  bool wifiUp() { return WiFi.status() == WL_CONNECTED; }

  // GET /health — true if the backend answers. Fills `brain` ("loom"/"llm").
  bool health(String &brain) {
    HTTPClient http; WiFiClient client;
    if (!http.begin(client, url("/health"))) return false;
    http.setTimeout(6000);
    int code = http.GET();
    if (code != 200) { http.end(); return false; }
    String body = http.getString();
    http.end();
    brain = jsonStr(body, "brain");
    return true;
  }

  // POST /select {agent} — lock the agent in Loom.
  bool select(const String &agent) {
    HTTPClient http; WiFiClient client;
    if (!http.begin(client, url("/select"))) return false;
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(10000);
    int code = http.POST(String("{\"agent\":\"") + agent + "\"}");
    http.end();
    return code == 200;
  }

  // POST /voice (raw PCM) → stream the spoken reply to the amp.
  // Fills transcript/reply from response headers. Returns true on 200.
  bool talk(const int16_t *pcm, size_t samples, const String &agent,
            Audio &audio, String &transcript, String &reply) {
    HTTPClient http; WiFiClient client;
    String u = url("/voice");
    if (agent.length()) u += "?agent=" + urlEnc(agent);
    if (!http.begin(client, u)) return false;
    http.addHeader("Content-Type", "application/octet-stream");
    const char *keys[] = {"X-Transcript", "X-Reply"};
    http.collectHeaders(keys, 2);
    http.setTimeout(60000);

    int code = http.POST((uint8_t *)pcm, samples * sizeof(int16_t));
    if (code != 200) { http.end(); return false; }
    transcript = urlDec(http.header("X-Transcript"));
    reply      = urlDec(http.header("X-Reply"));
    streamToSpeaker(http, audio);
    http.end();
    return true;
  }

  // GET /speak?text=… → play it (connected cue, telnet `say`).
  bool speak(const String &text, Audio &audio) {
    HTTPClient http; WiFiClient client;
    if (!http.begin(client, url("/speak") + "?text=" + urlEnc(text))) return false;
    http.setTimeout(30000);
    int code = http.GET();
    if (code != 200) { http.end(); return false; }
    streamToSpeaker(http, audio);
    http.end();
    return true;
  }

private:
  Settings *_s = nullptr;

  String url(const char *path) {
    return String("http://") + _s->backendHost + ":" + _s->backendPort + path;
  }

  // Read the PCM body and push it to I2S. The backend sends a Content-Length, so
  // there are no chunk markers to trip over; we carry an odd byte across reads to
  // keep 16-bit samples aligned.
  void streamToSpeaker(HTTPClient &http, Audio &audio) {
    WiFiClient *stream = http.getStreamPtr();
    int total = http.getSize();     // Content-Length, or -1 if unknown
    int remaining = total;
    uint8_t buf[1024];
    uint8_t carry = 0; bool haveCarry = false;
    uint32_t idle = millis();

    while (total < 0 ? (stream->connected() || stream->available()) : remaining > 0) {
      int avail = stream->available();
      if (avail > 0) {
        idle = millis();
        int off = 0;
        if (haveCarry) { buf[0] = carry; off = 1; haveCarry = false; }
        int want = (int)sizeof(buf) - off;
        if (total >= 0 && want > remaining) want = remaining;
        if (want <= 0) want = 1;
        int n = stream->readBytes(buf + off, min(avail, want));
        if (total >= 0) remaining -= n;
        int bytes = off + n;
        int samples = bytes / 2;
        if (bytes & 1) { carry = buf[bytes - 1]; haveCarry = true; }
        if (samples) audio.writeSpk((int16_t *)buf, samples);
      } else {
        if (!stream->connected() && !stream->available()) break;
        if (millis() - idle > 12000) break;     // stalled — bail
        delay(2);
      }
    }
  }

  static String urlEnc(const String &s) {
    static const char *hex = "0123456789ABCDEF";
    String o;
    for (size_t i = 0; i < s.length(); i++) {
      char c = s[i];
      if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') o += c;
      else if (c == ' ') o += "%20";
      else { o += '%'; o += hex[(c >> 4) & 0xF]; o += hex[c & 0xF]; }
    }
    return o;
  }

  static String urlDec(const String &s) {
    String o;
    for (size_t i = 0; i < s.length(); i++) {
      char c = s[i];
      if (c == '%' && i + 2 < s.length()) {
        auto h = [](char x) -> int {
          if (x >= '0' && x <= '9') return x - '0';
          if (x >= 'A' && x <= 'F') return x - 'A' + 10;
          if (x >= 'a' && x <= 'f') return x - 'a' + 10;
          return 0;
        };
        o += (char)((h(s[i + 1]) << 4) | h(s[i + 2]));
        i += 2;
      } else o += c;
    }
    return o;
  }

  // Minimal "key":"value" scrape — enough for /health without a JSON lib.
  static String jsonStr(const String &json, const char *key) {
    String needle = String("\"") + key + "\":\"";
    int a = json.indexOf(needle);
    if (a < 0) return "";
    a += needle.length();
    int b = json.indexOf('"', a);
    return b < 0 ? "" : json.substring(a, b);
  }
};
