#pragma once
#include <WiFi.h>
#include <WiFiManager.h>   // Library Manager: "WiFiManager" by tzapu
#include "config.h"
#include "settings.h"

// Captive-portal provisioning.
//
// On boot we try the saved WiFi. If there's none (first run) or it won't join,
// the pad raises the "LoomPad-Setup" access point and serves a portal: connect
// a phone/laptop to it and a page pops up (captive) listing the WiFi networks
// around you, plus fields for the Loom backend IP + telnet port. Save, and the
// pad joins your WiFi and remembers everything in flash — so this only happens
// once (or after a reset). autoConnect() blocks here until it's connected, which
// is why the portal parameters can live on the stack.
class Provision {
public:
  // Returns true once WiFi is connected. `portalColour` (optional) is a callback
  // the caller uses to light the status LED while the portal is open.
  bool run(Settings &s) {
    char portStr[8], telnetStr[8];
    snprintf(portStr, sizeof(portStr), "%u", s.backendPort);
    snprintf(telnetStr, sizeof(telnetStr), "%u", s.telnetPort);

    WiFiManagerParameter pHost("host", "Loom backend IP (your Mac)", s.backendHost, 40);
    WiFiManagerParameter pPort("port", "Backend port", portStr, 6);
    WiFiManagerParameter pTelnet("telnet", "Telnet port (for debug)", telnetStr, 6);

    _wm.setTitle("Loom Pad");
    _wm.addParameter(&pHost);
    _wm.addParameter(&pPort);
    _wm.addParameter(&pTelnet);
    _wm.setConfigPortalBlocking(true);
    _wm.setConfigPortalTimeout(0);          // stay open until configured
    _wm.setBreakAfterConfig(true);

    bool ok = strlen(PORTAL_AP_PASS)
                ? _wm.autoConnect(PORTAL_AP_NAME, PORTAL_AP_PASS)
                : _wm.autoConnect(PORTAL_AP_NAME);

    // Persist whatever the portal collected (harmless if nothing changed).
    uint16_t port = (uint16_t)atoi(pPort.getValue());
    uint16_t telnet = (uint16_t)atoi(pTelnet.getValue());
    s.set(pHost.getValue(),
          port ? port : s.backendPort,
          telnet ? telnet : s.telnetPort);

    return ok && WiFi.status() == WL_CONNECTED;
  }

  // Wipe the saved WiFi so the next boot re-opens the portal.
  void resetWifi() { _wm.resetSettings(); }

private:
  WiFiManager _wm;
};
