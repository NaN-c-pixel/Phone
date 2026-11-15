#!/usr/bin/env python3
"""SmolAI browser bridge: serve a mobile-friendly UI and proxy to local Ollama."""
import json
import os
import secrets
import socket
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
HOST = "0.0.0.0"
PORT = int(os.getenv("SMOLAI_PORT", "8765"))
TOKEN = secrets.token_urlsafe(18)

def post_json(url, payload, headers=None, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[SmolAI]", fmt % args)

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        page = WEB / "index.html"
        body = page.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return
        if self.headers.get("X-SmolAI-Token", "") != TOKEN:
            self.send_json(401, {"error": "Wrong access token. Copy the token shown in the laptop terminal."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 100_000:
                self.send_json(400, {"error": "Request size is invalid."})
                return
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            messages = data.get("messages", [])
            if not isinstance(messages, list) or not messages:
                self.send_json(400, {"error": "No messages provided."})
                return
            # Keep requests small for low-memory devices.
            messages = messages[-9:]
            mode = data.get("mode", "local")
            if mode == "local":
                host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
                model = os.getenv("OLLAMA_MODEL", "tinyllama")
                result = post_json(host + "/api/chat",
                    {"model": model, "messages": messages, "stream": False}, timeout=240)
                answer = result.get("message", {}).get("content", "").strip()
            elif mode == "cloud":
                key = os.getenv("CLOUD_API_KEY", "").strip()
                if not key:
                    self.send_json(400, {"error": "Cloud is not configured. Use local mode or configure .env on the laptop."})
                    return
                base = os.getenv("CLOUD_BASE_URL", "https://api.openai.com/v1").rstrip("/")
                model = os.getenv("CLOUD_MODEL", "gpt-4o-mini")
                result = post_json(base + "/chat/completions",
                    {"model": model, "messages": messages, "stream": False},
                    {"Authorization": "Bearer " + key}, timeout=120)
                answer = result["choices"][0]["message"]["content"].strip()
            else:
                self.send_json(400, {"error": "Unknown mode."})
                return
            self.send_json(200, {"answer": answer})
        except urllib.error.URLError as exc:
            self.send_json(502, {"error": "Could not reach the AI service. Check that Ollama is running. " + str(exc)})
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})

def lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()

if __name__ == "__main__":
    ip = lan_ip()
    print("\nSMOLAI WEB // LOCAL NETWORK")
    print("============================")
    print("On this laptop: http://127.0.0.1:" + str(PORT))
    print("On phone/tablet on same Wi-Fi: http://" + ip + ":" + str(PORT))
    print("\nACCESS TOKEN (keep private):")
    print(TOKEN)
    print("\nLocal mode sends prompts only to Ollama on this laptop.")
    print("Cloud mode is separate and sends prompts to your configured provider.")
    print("Keep this window open. Press Ctrl+C to stop.\n")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
