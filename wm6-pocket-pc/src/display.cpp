// Windows Mobile 6 style UI on a 2.8" ILI9341 240x320 SPI display (no touch).
// Navigation with 5 buttons: UP, DOWN, OK, LEFT softkey, RIGHT softkey.
//
// Wiring (ESP32-S3):            Buttons (other leg to GND, internal pull-ups used):
//   TFT VCC  -> 3V3               UP    -> GPIO4
//   TFT GND  -> GND               DOWN  -> GPIO5
//   TFT CS   -> GPIO10            LEFT  -> GPIO6   (left softkey)
//   TFT RESET-> GPIO8             RIGHT -> GPIO7   (right softkey)
//   TFT DC   -> GPIO9             OK    -> GPIO15
//   TFT MOSI -> GPIO11
//   TFT SCK  -> GPIO12
//   TFT LED  -> GPIO14 (backlight; or straight to 3V3)
//   TFT MISO -> GPIO13 (optional)

#include "display.h"
#include "shared.h"
#include <WiFi.h>
#include <LittleFS.h>
#include <ArduinoJson.h>
#include <time.h>

#define LGFX_USE_V1
#include <LovyanGFX.hpp>

// ---------- pins ----------
static const int PIN_SCLK = 12, PIN_MOSI = 11, PIN_MISO = 13;
static const int PIN_DC = 9, PIN_CS = 10, PIN_RST = 8, PIN_BL = 14;
static const int BTN_PINS[5] = {4, 5, 15, 6, 7};  // UP, DOWN, OK, LEFT, RIGHT
enum { B_UP, B_DOWN, B_OK, B_L, B_R };

class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ILI9341 _panel;
  lgfx::Bus_SPI _bus;
  lgfx::Light_PWM _light;

 public:
  LGFX() {
    {
      auto c = _bus.config();
      c.spi_host = SPI2_HOST;
      c.spi_mode = 0;
      c.freq_write = 40000000;
      c.freq_read = 16000000;
      c.pin_sclk = PIN_SCLK;
      c.pin_mosi = PIN_MOSI;
      c.pin_miso = PIN_MISO;
      c.pin_dc = PIN_DC;
      _bus.config(c);
      _panel.setBus(&_bus);
    }
    {
      auto c = _panel.config();
      c.pin_cs = PIN_CS;
      c.pin_rst = PIN_RST;
      c.pin_busy = -1;
      c.panel_width = 240;
      c.panel_height = 320;
      c.offset_x = 0;
      c.offset_y = 0;
      c.readable = false;
      c.invert = false;      // if colors look inverted, flip this
      c.rgb_order = false;   // if red and blue are swapped, flip this
      c.bus_shared = false;
      _panel.config(c);
    }
    {
      auto c = _light.config();
      c.pin_bl = PIN_BL;
      c.invert = false;
      c.freq = 44100;
      c.pwm_channel = 7;
      _light.config(c);
      _panel.setLight(&_light);
    }
    setPanel(&_panel);
  }
};

static LGFX lcd;
static lgfx::LGFX_Sprite fb(&lcd);  // full-frame buffer in PSRAM, no flicker

static const int W = 240, H = 320, TITLE_H = 26, SOFT_H = 24;
static const int BODY_Y = TITLE_H, BODY_H = H - TITLE_H - SOFT_H;

static inline uint16_t C(uint8_t r, uint8_t g, uint8_t b) { return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3); }
static const uint16_t WHITE = C(255, 255, 255), BLACK = C(0, 0, 0), SEL = C(29, 74, 156), LINE = C(159, 178, 212),
                      NAVY = C(29, 63, 122), GREY = C(100, 100, 100), PALE = C(233, 238, 247);

// ---------- state ----------
enum Screen { S_TODAY, S_NOTES, S_NOTE, S_CHAT, S_WIFI, S_ABOUT };
static Screen scr = S_TODAY;
static bool menuOpen = false, dirty = true;
static int menuIdx = 0, todayIdx = 0, noteIdx = 0, scroll = 0;
static uint32_t lastDraw = 0;
static std::vector<String> notes;

struct MenuItem { const char *name; Screen target; };
static const MenuItem MENU[] = {
    {"Today", S_TODAY}, {"Messenger", S_CHAT}, {"Notes", S_NOTES}, {"Wi-Fi", S_WIFI}, {"About", S_ABOUT}};
static const int MENU_N = sizeof(MENU) / sizeof(MENU[0]);

// ---------- helpers ----------
static void gradient(int x, int y, int w, int h, uint16_t r1, uint16_t g1, uint16_t b1, uint16_t r2, uint16_t g2, uint16_t b2) {
  for (int i = 0; i < h; i++) {
    int t = h > 1 ? i * 255 / (h - 1) : 0;
    fb.drawFastHLine(x, y + i, w, C(r1 + (r2 - r1) * t / 255, g1 + (g2 - g1) * t / 255, b1 + (b2 - b1) * t / 255));
  }
}

static void drawFlag(int x, int y) {
  fb.fillRect(x, y, 6, 6, C(242, 80, 34));
  fb.fillRect(x + 7, y, 6, 6, C(127, 186, 0));
  fb.fillRect(x, y + 7, 6, 6, C(0, 164, 239));
  fb.fillRect(x + 7, y + 7, 6, 6, C(255, 185, 0));
}

static bool timeValid() { return time(nullptr) > 1700000000; }

static String clockStr() {
  if (!timeValid()) return "--:--";
  struct tm t;
  time_t n = time(nullptr);
  localtime_r(&n, &t);
  char b[12];
  strftime(b, sizeof(b), "%I:%M %p", &t);
  return b[0] == '0' ? String(b + 1) : String(b);
}

static void titleBar(const char *title, bool showStart) {
  gradient(0, 0, W, TITLE_H, 91, 139, 214, 29, 74, 156);
  fb.drawFastHLine(0, TITLE_H - 1, W, C(18, 56, 119));
  fb.setFont(&fonts::FreeSansBold9pt7b);
  fb.setTextColor(WHITE);
  fb.setTextDatum(lgfx::middle_left);
  drawFlag(6, 6);
  fb.drawString(showStart ? "Start" : title, 24, TITLE_H / 2);
  fb.setFont(&fonts::FreeSans9pt7b);
  fb.setTextDatum(lgfx::middle_right);
  fb.drawString(clockStr(), W - 6, TITLE_H / 2);
}

static void softBar(const char *l, const char *r) {
  int y = H - SOFT_H;
  gradient(0, y, W, SOFT_H, 233, 238, 247, 185, 200, 226);
  fb.drawFastHLine(0, y, W, LINE);
  fb.setFont(&fonts::FreeSans9pt7b);
  fb.setTextColor(BLACK);
  fb.setTextDatum(lgfx::middle_left);
  fb.drawString(l, 8, y + SOFT_H / 2);
  fb.setTextDatum(lgfx::middle_right);
  fb.drawString(r, W - 8, y + SOFT_H / 2);
}

static void header(int y, const char *txt) {
  gradient(0, y, W, 20, 233, 238, 247, 205, 217, 238);
  fb.drawFastHLine(0, y + 19, W, LINE);
  fb.setFont(&fonts::FreeSansBold9pt7b);
  fb.setTextColor(NAVY);
  fb.setTextDatum(lgfx::middle_left);
  fb.drawString(txt, 6, y + 10);
}

// one list row; selected rows are inverted like WM6
static void row(int y, int h, const String &main, const String &sub, bool sel) {
  if (sel) fb.fillRect(0, y, W, h, SEL);
  fb.drawFastHLine(0, y + h - 1, W, sel ? SEL : C(219, 227, 242));
  fb.setFont(&fonts::FreeSans9pt7b);
  fb.setTextDatum(lgfx::middle_left);
  fb.setTextColor(sel ? WHITE : BLACK);
  String m = main;
  while (m.length() > 3 && fb.textWidth(m) > W - 12) m.remove(m.length() - 1);
  fb.drawString(m, 8, y + (sub.length() ? h / 3 : h / 2));
  if (sub.length()) {
    fb.setTextColor(sel ? C(220, 224, 240) : GREY);
    String s = sub;
    while (s.length() > 3 && fb.textWidth(s) > W - 12) s.remove(s.length() - 1);
    fb.drawString(s, 8, y + h * 2 / 3 + 1);
  }
}

// word-wrap `s` to width w, appending lines to `out`
static void wrap(const String &s, int w, std::vector<String> &out) {
  String line, word;
  auto flush = [&]() {
    if (line.length()) out.push_back(line);
    line = "";
  };
  for (unsigned i = 0; i <= s.length(); i++) {
    char c = i < s.length() ? s[i] : ' ';
    if (c == '\n') {
      line = line.length() ? line + " " + word : word;
      word = "";
      flush();
    } else if (c == ' ') {
      if (word.length()) {
        String t = line.length() ? line + " " + word : word;
        if (fb.textWidth(t) > w && line.length()) {
          flush();
          line = word;
        } else {
          line = t;
        }
        word = "";
      }
    } else {
      word += c;
      while (fb.textWidth(word) > w && word.length() > 1) {  // very long word
        flush();
        String head = word.substring(0, word.length() - 1);
        out.push_back(head);
        word = word.substring(word.length() - 1);
      }
    }
  }
  flush();
}

// ---------- data ----------
static void loadNotes() {
  notes.clear();
  File f = LittleFS.open("/notes.json", "r");
  if (!f) return;
  JsonDocument d;
  if (deserializeJson(d, f)) return;
  for (JsonObject o : d.as<JsonArray>()) notes.push_back(String((const char *)(o["text"] | "")));
}

static String kb(size_t n) {
  return n >= 1048576 ? String(n / 1048576.0, 1) + " MB" : String(n / 1024.0, 0) + " KB";
}

// ---------- screens ----------
static void drawToday() {
  titleBar("Today", true);
  fb.fillRect(0, BODY_Y, W, BODY_H, WHITE);
  gradient(0, BODY_Y, W, 90, 223, 233, 248, 255, 255, 255);

  fb.setTextColor(NAVY);
  fb.setTextDatum(lgfx::top_left);
  fb.setFont(&fonts::FreeSansBold12pt7b);
  if (timeValid()) {
    struct tm t;
    time_t n = time(nullptr);
    localtime_r(&n, &t);
    char b[40];
    strftime(b, sizeof(b), "%A, %B %d", &t);
    fb.drawString(b, 8, BODY_Y + 6);
  } else {
    fb.drawString("Open the web UI", 8, BODY_Y + 6);
  }
  fb.setFont(&fonts::FreeSans18pt7b);
  fb.setTextColor(SEL);
  fb.drawString(clockStr(), 8, BODY_Y + 36);

  String wifi = WiFi.status() == WL_CONNECTED ? WiFi.SSID() : String("Access point mode");
  String wsub = (WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : WiFi.softAPIP().toString()) + " - " +
                String(WiFi.softAPgetStationNum()) + " connected";
  int y = BODY_Y + 92, h = 38;
  row(y, h, "Wi-Fi: " + wifi, wsub, todayIdx == 0);
  row(y + h, h, "Messenger", String(chatLog.size()) + " message" + (chatLog.size() == 1 ? "" : "s"), todayIdx == 1);
  static uint32_t notesAt = 0;
  if (millis() - notesAt > 5000 || notesAt == 0) {  // don't hit flash every redraw
    loadNotes();
    notesAt = millis();
  }
  row(y + h * 2, h, "Notes", String(notes.size()) + " note" + (notes.size() == 1 ? "" : "s"), todayIdx == 2);
  row(y + h * 3, h, "Memory " + kb(ESP.getFreeHeap()) + " free", "PSRAM " + kb(ESP.getFreePsram()) + " free", todayIdx == 3);
  softBar("Start", "About");
}

static void drawNotes() {
  titleBar("Notes", false);
  fb.fillRect(0, BODY_Y, W, BODY_H, WHITE);
  header(BODY_Y, "All Folders");
  if (notes.empty()) {
    fb.setFont(&fonts::FreeSans9pt7b);
    fb.setTextColor(GREY);
    fb.setTextDatum(lgfx::middle_center);
    fb.drawString("No notes. Create them in the web UI.", W / 2, H / 2);
  } else {
    const int rh = 30, vis = (BODY_H - 20) / rh;
    int top = noteIdx >= vis ? noteIdx - vis + 1 : 0;
    for (int i = 0; i < vis && top + i < (int)notes.size(); i++) {
      String first = notes[top + i];
      int nl = first.indexOf('\n');
      if (nl >= 0) first = first.substring(0, nl);
      row(BODY_Y + 20 + i * rh, rh, first.length() ? first : "Untitled", "", top + i == noteIdx);
    }
  }
  softBar("Open", "Back");
}

static void drawNote() {
  titleBar("Notes", false);
  fb.fillRect(0, BODY_Y, W, BODY_H, WHITE);
  fb.setFont(&fonts::FreeSans9pt7b);
  std::vector<String> lines;
  if (noteIdx < (int)notes.size()) wrap(notes[noteIdx], W - 16, lines);
  const int lh = 18, vis = (BODY_H - 8) / lh;
  int maxScroll = max(0, (int)lines.size() - vis);
  scroll = constrain(scroll, 0, maxScroll);
  fb.setTextColor(BLACK);
  fb.setTextDatum(lgfx::top_left);
  for (int i = 0; i < vis && scroll + i < (int)lines.size(); i++) fb.drawString(lines[scroll + i], 8, BODY_Y + 6 + i * lh);
  softBar("", "Back");
}

static void drawChat() {
  titleBar("Messenger", false);
  fb.fillRect(0, BODY_Y, W, BODY_H, C(244, 247, 252));
  fb.setFont(&fonts::FreeSans9pt7b);
  struct L { String s; bool head; };
  std::vector<L> lines;
  for (auto &m : chatLog) {
    lines.push_back({m.from, true});
    std::vector<String> w;
    wrap(m.text, W - 20, w);
    for (auto &s : w) lines.push_back({s, false});
  }
  if (lines.empty()) {
    fb.setTextColor(GREY);
    fb.setTextDatum(lgfx::middle_center);
    fb.drawString("No messages yet.", W / 2, H / 2 - 10);
    fb.drawString("Send them from the web UI.", W / 2, H / 2 + 12);
  } else {
    const int lh = 17, vis = (BODY_H - 6) / lh;
    int maxScroll = max(0, (int)lines.size() - vis);
    scroll = constrain(scroll, 0, maxScroll);
    int start = maxScroll - scroll;  // scroll=0 -> newest at bottom
    fb.setTextDatum(lgfx::top_left);
    for (int i = 0; i < vis && start + i < (int)lines.size(); i++) {
      auto &l = lines[start + i];
      fb.setTextColor(l.head ? NAVY : BLACK);
      fb.setFont(l.head ? &fonts::FreeSansBold9pt7b : &fonts::FreeSans9pt7b);
      fb.drawString(l.s, l.head ? 6 : 14, BODY_Y + 4 + i * lh);
    }
  }
  softBar("", "Back");
}

static void kvRow(int y, const char *k, const String &v) {
  fb.setFont(&fonts::FreeSansBold9pt7b);
  fb.setTextColor(NAVY);
  fb.setTextDatum(lgfx::top_left);
  fb.drawString(k, 8, y);
  fb.setFont(&fonts::FreeSans9pt7b);
  fb.setTextColor(BLACK);
  fb.drawString(v, 8, y + 16);
  fb.drawFastHLine(0, y + 36, W, C(227, 233, 245));
}

static void drawAbout() {
  titleBar("About", false);
  fb.fillRect(0, BODY_Y, W, BODY_H, WHITE);
  header(BODY_Y, "Device information");
  int y = BODY_Y + 24;
  kvRow(y, "Processor", String(ESP.getChipModel()) + ", " + ESP.getChipCores() + " cores, " + ESP.getCpuFreqMHz() + " MHz");
  kvRow(y + 38, "Temperature / uptime", String(temperatureRead(), 1) + " C, " + String(millis() / 60000) + " min");
  kvRow(y + 76, "Program memory", kb(ESP.getHeapSize() - ESP.getFreeHeap()) + " of " + kb(ESP.getHeapSize()));
  kvRow(y + 114, "PSRAM", kb(ESP.getPsramSize() - ESP.getFreePsram()) + " of " + kb(ESP.getPsramSize()));
  kvRow(y + 152, "Storage", kb(LittleFS.usedBytes()) + " of " + kb(LittleFS.totalBytes()));
  softBar("", "Back");
}

static void drawWifi() {
  titleBar("Wireless", false);
  fb.fillRect(0, BODY_Y, W, BODY_H, WHITE);
  header(BODY_Y, "Connections");
  int y = BODY_Y + 24;
  kvRow(y, "Access point (this device)", "WM6-Pocket  " + WiFi.softAPIP().toString());
  kvRow(y + 38, "Devices connected", String(WiFi.softAPgetStationNum()));
  bool on = WiFi.status() == WL_CONNECTED;
  kvRow(y + 76, "Internet network", on ? WiFi.SSID() + "  " + WiFi.localIP().toString() : String("Not connected"));
  kvRow(y + 114, "Signal", on ? String(WiFi.RSSI()) + " dBm" : String("-"));
  fb.setFont(&fonts::FreeSans9pt7b);
  fb.setTextColor(GREY);
  fb.setTextDatum(lgfx::top_left);
  fb.drawString("Join a network from the web UI", 8, y + 160);
  softBar("", "Back");
}

static void drawMenu() {
  fb.fillRect(0, BODY_Y, 170, BODY_H, WHITE);
  fb.drawRect(0, BODY_Y, 170, BODY_H, SEL);
  const char *icons[] = {"", "", "", "", ""};
  (void)icons;
  for (int i = 0; i < MENU_N; i++) row(BODY_Y + 2 + i * 34, 34, MENU[i].name, "", i == menuIdx);
  softBar("Select", "Close");
}

static void render() {
  switch (scr) {
    case S_TODAY: drawToday(); break;
    case S_NOTES: drawNotes(); break;
    case S_NOTE: drawNote(); break;
    case S_CHAT: drawChat(); break;
    case S_WIFI: drawWifi(); break;
    case S_ABOUT: drawAbout(); break;
  }
  if (menuOpen) {
    titleBar("Start", true);
    drawMenu();
  }
  fb.pushSprite(0, 0);
}

// ---------- input ----------
static void go(Screen s) {
  scr = s;
  menuOpen = false;
  scroll = 0;
  if (s == S_NOTES) {
    loadNotes();
    noteIdx = 0;
  }
  dirty = true;
}

static void onButton(int b) {
  dirty = true;
  if (menuOpen) {
    if (b == B_UP) menuIdx = (menuIdx + MENU_N - 1) % MENU_N;
    else if (b == B_DOWN) menuIdx = (menuIdx + 1) % MENU_N;
    else if (b == B_OK || b == B_L) go(MENU[menuIdx].target);
    else if (b == B_R) menuOpen = false;
    return;
  }
  switch (scr) {
    case S_TODAY:
      if (b == B_UP) todayIdx = (todayIdx + 3) % 4;
      else if (b == B_DOWN) todayIdx = (todayIdx + 1) % 4;
      else if (b == B_L) menuOpen = true;
      else if (b == B_R) go(S_ABOUT);
      else if (b == B_OK) go(todayIdx == 0 ? S_WIFI : todayIdx == 1 ? S_CHAT : todayIdx == 2 ? S_NOTES : S_ABOUT);
      break;
    case S_NOTES:
      if (b == B_UP && noteIdx > 0) noteIdx--;
      else if (b == B_DOWN && noteIdx + 1 < (int)notes.size()) noteIdx++;
      else if ((b == B_OK || b == B_L) && !notes.empty()) { scr = S_NOTE; scroll = 0; }
      else if (b == B_R) go(S_TODAY);
      break;
    case S_NOTE:
      if (b == B_UP) scroll--;
      else if (b == B_DOWN) scroll++;
      else if (b == B_R || b == B_OK) scr = S_NOTES;
      break;
    case S_CHAT:
      if (b == B_UP) scroll++;  // older
      else if (b == B_DOWN) scroll--;
      else if (b == B_R) go(S_TODAY);
      break;
    default:
      if (b == B_R || b == B_OK) go(S_TODAY);
  }
}

void displayInit() {
  for (int p : BTN_PINS) pinMode(p, INPUT_PULLUP);
  lcd.init();
  lcd.setRotation(0);
  lcd.setBrightness(200);
  lcd.fillScreen(BLACK);
  fb.setPsram(true);
  fb.setColorDepth(16);
  if (!fb.createSprite(W, H)) {
    Serial.println("Frame buffer allocation failed");
    return;
  }
  // splash
  fb.fillScreen(WHITE);
  gradient(0, 0, W, H, 223, 233, 248, 255, 255, 255);
  drawFlag(W / 2 - 13, 110);
  fb.setFont(&fonts::FreeSansBold12pt7b);
  fb.setTextColor(NAVY);
  fb.setTextDatum(lgfx::top_center);
  fb.drawString("Pocket PC", W / 2, 145);
  fb.setFont(&fonts::FreeSans9pt7b);
  fb.drawString("ESP32-S3", W / 2, 175);
  fb.pushSprite(0, 0);
  delay(1200);
}

void displayLoop() {
  static uint32_t lastT[5] = {0}, rep[5] = {0};
  static bool down[5] = {false};
  uint32_t now = millis();
  for (int i = 0; i < 5; i++) {
    bool d = digitalRead(BTN_PINS[i]) == LOW;
    if (d && !down[i] && now - lastT[i] > 40) {
      lastT[i] = now;
      rep[i] = now + 400;
      onButton(i);
    } else if (d && down[i] && i < 2 && now >= rep[i]) {  // hold UP/DOWN to repeat
      rep[i] = now + 120;
      onButton(i);
    }
    down[i] = d;
  }
  // clock and live data refresh once a second
  if (dirty || now - lastDraw > 1000) {
    dirty = false;
    lastDraw = now;
    if (fb.width() > 0) render();
  }
}
