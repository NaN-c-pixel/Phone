// ESP32-S3 "Pocket PC" - serves a Windows Mobile 6 styled UI over Wi-Fi.
// Connect to the Wi-Fi network WM6-Pocket (password: pocketpc1) and open http://192.168.4.1
// or http://pocketpc.local

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <LittleFS.h>
#include <ESPmDNS.h>
#include <ArduinoJson.h>
#include <sys/time.h>
#include "shared.h"
#include "display.h"

static const char *AP_SSID = "WM6-Pocket";
static const char *AP_PASS = "pocketpc1";  // min 8 chars

WebServer server(80);

// ---------- helpers ----------
String readFile(const char *path) {
  File f = LittleFS.open(path, "r");
  if (!f) return "";
  String s = f.readString();
  f.close();
  return s;
}

bool writeFile(const char *path, const String &data) {
  File f = LittleFS.open(path, "w");
  if (!f) return false;
  f.print(data);
  f.close();
  return true;
}

void sendJson(const JsonDocument &doc, int code = 200) {
  String out;
  serializeJson(doc, out);
  server.send(code, "application/json", out);
}

bool safePath(const String &p) {
  return p.startsWith("/") && p.indexOf("..") < 0;
}

// ---------- wifi ----------
void connectSaved() {
  String raw = readFile("/wifi.json");
  if (raw.isEmpty()) return;
  JsonDocument d;
  if (deserializeJson(d, raw)) return;
  const char *ssid = d["ssid"] | "";
  const char *pass = d["pass"] | "";
  if (strlen(ssid)) {
    WiFi.begin(ssid, pass);
    Serial.printf("Connecting to %s\n", ssid);
  }
}

// ---------- api ----------
void apiSys() {
  JsonDocument d;
  d["model"] = ESP.getChipModel();
  d["cores"] = ESP.getChipCores();
  d["mhz"] = ESP.getCpuFreqMHz();
  d["heapFree"] = ESP.getFreeHeap();
  d["heapTotal"] = ESP.getHeapSize();
  d["psramFree"] = ESP.getFreePsram();
  d["psramTotal"] = ESP.getPsramSize();
  d["flash"] = ESP.getFlashChipSize();
  d["fsUsed"] = LittleFS.usedBytes();
  d["fsTotal"] = LittleFS.totalBytes();
  d["uptime"] = millis() / 1000;
  d["tempC"] = temperatureRead();
  d["epoch"] = (uint32_t)time(nullptr);
  d["apIp"] = WiFi.softAPIP().toString();
  d["staConnected"] = WiFi.status() == WL_CONNECTED;
  d["staSsid"] = WiFi.SSID();
  d["staIp"] = WiFi.localIP().toString();
  d["rssi"] = WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0;
  d["clients"] = WiFi.softAPgetStationNum();
  sendJson(d);
}

void apiTime() {
  JsonDocument d;
  if (deserializeJson(d, server.arg("plain"))) {
    server.send(400, "text/plain", "bad json");
    return;
  }
  struct timeval tv;
  tv.tv_sec = (time_t)(d["epoch"] | 0);
  tv.tv_usec = 0;
  settimeofday(&tv, nullptr);
  server.send(200, "text/plain", "ok");
}

void apiNotesGet() {
  String s = readFile("/notes.json");
  if (s.isEmpty()) s = "[]";
  server.send(200, "application/json", s);
}

void apiNotesPut() {
  JsonDocument d;  // validate before writing
  if (deserializeJson(d, server.arg("plain")) || !d.is<JsonArray>()) {
    server.send(400, "text/plain", "bad json");
    return;
  }
  server.send(writeFile("/notes.json", server.arg("plain")) ? 200 : 500, "text/plain", "ok");
}

void apiFiles() {
  JsonDocument d;
  JsonArray arr = d.to<JsonArray>();
  File root = LittleFS.open("/");
  for (File f = root.openNextFile(); f; f = root.openNextFile()) {
    JsonObject o = arr.add<JsonObject>();
    o["name"] = String("/") + f.name();
    o["size"] = f.size();
    o["dir"] = f.isDirectory();
  }
  sendJson(d);
}

void apiFileGet() {
  String p = server.arg("path");
  if (!safePath(p) || !LittleFS.exists(p)) {
    server.send(404, "text/plain", "not found");
    return;
  }
  File f = LittleFS.open(p, "r");
  server.streamFile(f, "text/plain");
  f.close();
}

void apiFilePut() {
  String p = server.arg("path");
  if (!safePath(p) || p == "/wifi.json") {
    server.send(400, "text/plain", "bad path");
    return;
  }
  server.send(writeFile(p.c_str(), server.arg("plain")) ? 200 : 500, "text/plain", "ok");
}

void apiFileDelete() {
  String p = server.arg("path");
  if (!safePath(p) || !LittleFS.exists(p)) {
    server.send(404, "text/plain", "not found");
    return;
  }
  LittleFS.remove(p);
  server.send(200, "text/plain", "ok");
}

void apiScan() {
  int n = WiFi.scanNetworks();
  JsonDocument d;
  JsonArray arr = d.to<JsonArray>();
  for (int i = 0; i < n; i++) {
    JsonObject o = arr.add<JsonObject>();
    o["ssid"] = WiFi.SSID(i);
    o["rssi"] = WiFi.RSSI(i);
    o["open"] = WiFi.encryptionType(i) == WIFI_AUTH_OPEN;
  }
  WiFi.scanDelete();
  sendJson(d);
}

void apiConnect() {
  JsonDocument d;
  if (deserializeJson(d, server.arg("plain"))) {
    server.send(400, "text/plain", "bad json");
    return;
  }
  String ssid = d["ssid"] | "";
  String pass = d["pass"] | "";
  WiFi.begin(ssid.c_str(), pass.c_str());
  uint32_t t = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t < 10000) delay(200);
  bool ok = WiFi.status() == WL_CONNECTED;
  if (ok) {
    JsonDocument s;
    s["ssid"] = ssid;
    s["pass"] = pass;
    String out;
    serializeJson(s, out);
    writeFile("/wifi.json", out);
  }
  JsonDocument r;
  r["ok"] = ok;
  r["ip"] = WiFi.localIP().toString();
  sendJson(r);
}

void apiReboot() {
  server.send(200, "text/plain", "rebooting");
  delay(300);
  ESP.restart();
}

// ---------- messenger (local chat for everyone on the board's network) ----------
#include <vector>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

std::vector<ChatMsg> chatLog;
static uint32_t chatNext = 1;
static const size_t CHAT_MAX = 200;

void apiChatGet() {
  uint32_t since = server.arg("since").toInt();
  uint32_t last = chatNext - 1;
  if (since > last) since = 0;  // board rebooted, resend everything
  JsonDocument d;
  d["last"] = last;
  JsonArray arr = d["msgs"].to<JsonArray>();
  for (auto &m : chatLog) {
    if (m.id <= since) continue;
    JsonObject o = arr.add<JsonObject>();
    o["id"] = m.id;
    o["from"] = m.from;
    o["text"] = m.text;
    o["t"] = m.t;
  }
  sendJson(d);
}

void apiChatPost() {
  JsonDocument d;
  if (deserializeJson(d, server.arg("plain"))) {
    server.send(400, "text/plain", "bad json");
    return;
  }
  String from = d["from"] | "Guest";
  String text = d["text"] | "";
  from.trim();
  text.trim();
  if (text.isEmpty()) {
    server.send(400, "text/plain", "empty");
    return;
  }
  if (from.isEmpty()) from = "Guest";
  if (from.length() > 20) from = from.substring(0, 20);
  if (text.length() > 500) text = text.substring(0, 500);
  chatLog.push_back({chatNext++, from, text, (uint32_t)time(nullptr)});
  if (chatLog.size() > CHAT_MAX) chatLog.erase(chatLog.begin());
  server.send(200, "text/plain", "ok");
}

// ---------- browser proxy (needs the board to be joined to a Wi-Fi network) ----------
// HTTPS certificates are NOT verified here (setInsecure), so treat it as a casual text browser.
void apiBrowse() {
  String url = server.arg("url");
  if (!(url.startsWith("http://") || url.startsWith("https://"))) {
    server.send(400, "text/plain", "Only http and https addresses are supported.");
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    server.send(503, "text/plain", "The device is not connected to the internet. Open Wireless Manager and join a network first.");
    return;
  }
  WiFiClientSecure sc;
  sc.setInsecure();
  WiFiClient pc;
  HTTPClient http;
  bool ok = url.startsWith("https://") ? http.begin(sc, url) : http.begin(pc, url);
  if (!ok) {
    server.send(400, "text/plain", "Bad address.");
    return;
  }
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.setTimeout(8000);
  http.useHTTP10(true);  // avoids chunked encoding so the body can be read with a size cap
  http.setUserAgent("Mozilla/5.0 (Windows CE; PPC; 240x320) PocketBrowser/1.0");
  const char *keys[] = {"Content-Type"};
  http.collectHeaders(keys, 1);

  int code = http.GET();
  if (code <= 0) {
    server.send(502, "text/plain", String("Could not load page: ") + HTTPClient::errorToString(code));
    http.end();
    return;
  }
  String ct = http.header("Content-Type");
  if (ct.length() && ct.indexOf("text") < 0 && ct.indexOf("xml") < 0 && ct.indexOf("json") < 0) {
    server.send(415, "text/plain", "This browser only shows text pages (" + ct + ").");
    http.end();
    return;
  }

  const size_t MAXB = 150000;
  String body;
  body.reserve(32768);
  WiFiClient *s = http.getStreamPtr();
  uint8_t buf[1024];
  uint32_t t0 = millis();
  while (body.length() < MAXB && millis() - t0 < 10000) {
    int avail = s->available();
    if (avail > 0) {
      int n = s->readBytes(buf, min(avail, (int)sizeof(buf)));
      body.concat((const char *)buf, n);
    } else if (!s->connected()) {
      break;
    } else {
      delay(5);
    }
  }
  http.end();
  server.sendHeader("X-Remote-Status", String(code));
  server.send(200, "text/html; charset=utf-8", body);
}

void serveIndex() {
  File f = LittleFS.open("/index.html", "r");
  if (!f) {
    server.send(500, "text/plain", "Upload the filesystem image first (pio run -t uploadfs)");
    return;
  }
  server.streamFile(f, "text/html");
  f.close();
}

void setup() {
  Serial.begin(115200);
  delay(300);

  if (!LittleFS.begin(true)) Serial.println("LittleFS mount failed");
  setenv("TZ", "ICT-7", 1);  // Vietnam time (UTC+7); change for your zone
  tzset();
  displayInit();

  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.printf("AP up: %s  http://%s\n", AP_SSID, WiFi.softAPIP().toString().c_str());
  connectSaved();

  MDNS.begin("pocketpc");

  server.on("/", HTTP_GET, serveIndex);
  server.on("/api/sys", HTTP_GET, apiSys);
  server.on("/api/time", HTTP_POST, apiTime);
  server.on("/api/notes", HTTP_GET, apiNotesGet);
  server.on("/api/notes", HTTP_PUT, apiNotesPut);
  server.on("/api/files", HTTP_GET, apiFiles);
  server.on("/api/file", HTTP_GET, apiFileGet);
  server.on("/api/file", HTTP_PUT, apiFilePut);
  server.on("/api/file", HTTP_DELETE, apiFileDelete);
  server.on("/api/scan", HTTP_GET, apiScan);
  server.on("/api/connect", HTTP_POST, apiConnect);
  server.on("/api/reboot", HTTP_POST, apiReboot);
  server.on("/api/chat", HTTP_GET, apiChatGet);
  server.on("/api/chat", HTTP_POST, apiChatPost);
  server.on("/api/browse", HTTP_GET, apiBrowse);
  server.serveStatic("/", LittleFS, "/", "max-age=300");
  server.onNotFound([]() { server.send(404, "text/plain", "404"); });
  server.begin();
}

void loop() {
  server.handleClient();
  displayLoop();
  delay(2);
}
