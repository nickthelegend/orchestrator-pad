#pragma once
#include <Arduino.h>
#include <Preferences.h>
#include "config.h"

// Runtime config, persisted in NVS (flash key/value). Written by the captive
// portal, read on every boot. WiFi credentials themselves are stored by
// WiFiManager separately; this holds where the backend lives.
struct Settings {
  char     backendHost[41] = DEFAULT_BACKEND_HOST;
  uint16_t backendPort     = DEFAULT_BACKEND_PORT;
  uint16_t telnetPort      = DEFAULT_TELNET_PORT;

  void load() {
    Preferences p;
    p.begin("loompad", true); // read-only
    String h = p.getString("host", DEFAULT_BACKEND_HOST);
    strncpy(backendHost, h.c_str(), sizeof(backendHost) - 1);
    backendHost[sizeof(backendHost) - 1] = 0;
    backendPort = p.getUShort("port", DEFAULT_BACKEND_PORT);
    telnetPort  = p.getUShort("telnet", DEFAULT_TELNET_PORT);
    p.end();
  }

  void save() {
    Preferences p;
    p.begin("loompad", false);
    p.putString("host", backendHost);
    p.putUShort("port", backendPort);
    p.putUShort("telnet", telnetPort);
    p.end();
  }

  void set(const char *host, uint16_t port, uint16_t telnet) {
    strncpy(backendHost, host, sizeof(backendHost) - 1);
    backendHost[sizeof(backendHost) - 1] = 0;
    if (port) backendPort = port;
    if (telnet) telnetPort = telnet;
    save();
  }

  // Wipe everything (used by the reset-provisioning gesture).
  static void erase() {
    Preferences p;
    p.begin("loompad", false);
    p.clear();
    p.end();
  }
};
