#pragma once
#include <Arduino.h>
#include <vector>

// Shared between main.cpp (web server) and display.cpp (little screen).
struct ChatMsg {
  uint32_t id;
  String from;
  String text;
  uint32_t t;
};
extern std::vector<ChatMsg> chatLog;
