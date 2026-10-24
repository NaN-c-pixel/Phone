# HungsOS AI bridge
# The ESP32-S3 does not run the LLM locally. It sends chat to a LAN model server.
# Default target: Ollama on a computer you control.

import socket
import gc
import json

try:
    from wifi_config import AI_HOST, AI_PORT, AI_MODEL
except ImportError:
    AI_HOST = ""
    AI_PORT = 11434
    AI_MODEL = "tinyllama"

AI_PATH = "/api/chat"
MAX_HISTORY = 8
MAX_TEXT = 900
TIMEOUT = 20

_history = []

def _clip(s):
    s = str(s).strip()
    return s if len(s) <= MAX_TEXT else s[:MAX_TEXT] + "..."

def clear():
    del _history[:]
    gc.collect()

def configured():
    return bool(AI_HOST)

def _http_post(host, port, path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = ("POST %s HTTP/1.1\r\nHost: %s:%d\r\n"
           "Content-Type: application/json\r\nContent-Length: %d\r\n"
           "Connection: close\r\n\r\n" % (path, host, port, len(data))).encode("ascii") + data
    addr = socket.getaddrinfo(host, port)[0][-1]
    s = socket.socket()
    s.settimeout(TIMEOUT)
    try:
        s.connect(addr)
        sent = 0
        while sent < len(req):
            n = s.send(req[sent:sent + 1024])
            if not n:
                raise OSError("socket closed")
            sent += n
        chunks = []
        while True:
            b = s.recv(1024)
            if not b:
                break
            chunks.append(b)
            if sum(len(x) for x in chunks) > 12000:
                break
        raw = b"".join(chunks)
    finally:
        s.close()
    head, sep, body = raw.partition(b"\r\n\r\n")
    if not sep:
        raise OSError("bad HTTP response")
    status = head.split(b"\r\n", 1)[0]
    if b" 200 " not in status:
        raise OSError("AI server returned " + status.decode("ascii", "ignore"))
    return json.loads(body.decode("utf-8"))

def ask(text):
    if not configured():
        return ("AI is not configured yet. Add AI_HOST, AI_PORT and AI_MODEL "
                "to wifi_config.py. For example, point AI_HOST at the PC "
                "running Ollama on your home Wi-Fi.")
    text = _clip(text)
    _history.append({"role": "user", "content": text})
    if len(_history) > MAX_HISTORY:
        del _history[:-MAX_HISTORY]
    payload = {
        "model": AI_MODEL,
        "messages": list(_history),
        "stream": False,
        "options": {"num_ctx": 1024, "temperature": 0.7}
    }
    try:
        gc.collect()
        data = _http_post(AI_HOST, int(AI_PORT), AI_PATH, payload)
        answer = _clip(data.get("message", {}).get("content", ""))
        if not answer:
            answer = "The AI server returned an empty answer."
        _history.append({"role": "assistant", "content": answer})
        if len(_history) > MAX_HISTORY:
            del _history[:-MAX_HISTORY]
        gc.collect()
        return answer
    except Exception as e:
        # Remove the unanswered user turn so a temporary network failure
        # does not poison the next conversation.
        if _history and _history[-1].get("role") == "user":
            _history.pop()
        gc.collect()
        return "AI server unavailable: " + str(e)
