#!/usr/bin/env python3
"""SmolAI: local-first terminal chat using Ollama and optional cloud API."""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_env():
    """Load simple KEY=VALUE settings from the local .env file."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def post_json(url, payload, headers=None, timeout=180):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ask_local(messages):
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "tinyllama")
    result = post_json(
        host + "/api/chat",
        {"model": model, "messages": messages, "stream": False},
        timeout=240,
    )
    return result.get("message", {}).get("content", "").strip()


def ask_cloud(messages):
    key = os.getenv("CLOUD_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Cloud mode is not configured. Copy .env.example to .env and "
            "configure a provider with the account owner's permission."
        )
    base = os.getenv("CLOUD_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("CLOUD_MODEL", "gpt-4o-mini")
    result = post_json(
        base + "/chat/completions",
        {"model": model, "messages": messages, "stream": False},
        headers={"Authorization": "Bearer " + key},
        timeout=120,
    )
    return result["choices"][0]["message"]["content"].strip()


def show_help():
    print("""
Commands:
  /local   Use Ollama on this laptop
  /cloud   Send the next messages to the configured cloud provider
  /clear   Clear the current conversation
  /help    Show this help
  /exit    Quit

SmolAI starts in local mode. It never silently uploads chats to the cloud.
Cloud API usage may cost money and is separate from a ChatGPT subscription.
""")


def main():
    load_env()
    mode = "local"
    system_message = {
        "role": "system",
        "content": "You are SmolAI, a helpful, concise assistant. Be honest about uncertainty.",
    }
    history = [system_message]

    print("\nSMOLAI // TERMINAL AI")
    print("====================")
    print("Local-first assistant | type /help for commands")
    print("Model:", os.getenv("OLLAMA_MODEL", "tinyllama"))
    print("Mode: LOCAL (no cloud upload)\n")

    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSmolAI> Bye!")
            break

        if not prompt:
            continue
        command = prompt.lower()
        if command in ("/exit", "/quit"):
            print("SmolAI> Bye!")
            break
        if command == "/help":
            show_help()
            continue
        if command == "/clear":
            history = [system_message]
            print("SmolAI> Conversation cleared.")
            continue
        if command == "/local":
            mode = "local"
            print("SmolAI> Local mode selected.")
            continue
        if command == "/cloud":
            mode = "cloud"
            print("SmolAI> Cloud mode selected. Messages will be sent to your configured provider.")
            continue

        history.append({"role": "user", "content": prompt})
        # Small rolling context to reduce RAM use and request size.
        messages = [system_message] + history[-8:]
        try:
            answer = ask_cloud(messages) if mode == "cloud" else ask_local(messages)
            print("\nSmolAI> " + (answer or "(empty response)") + "\n")
            history.append({"role": "assistant", "content": answer})
        except urllib.error.URLError as exc:
            print("\nSmolAI> Could not reach the AI service.")
            print("Check Ollama is running, or check your internet and cloud settings.")
            print("Details:", exc, "\n")
            history.pop()
        except (KeyError, IndexError, json.JSONDecodeError, RuntimeError) as exc:
            print("\nSmolAI>", exc, "\n")
            history.pop()
        except Exception as exc:
            print("\nSmolAI> Unexpected error:", exc, "\n")
            history.pop()


if __name__ == "__main__":
    main()
