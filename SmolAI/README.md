# SmolAI Lite

A tiny, local-first AI assistant with a terminal and a mobile-friendly browser interface.

## What works today

- Windows laptop: Python terminal and browser UI.
- Android / iPhone / iPad / other devices: open the browser UI from a device on the **same Wi-Fi** as the laptop.
- Local AI: Ollama on the laptop; the phone/tablet is just the screen and keyboard.
- Optional cloud AI: only after explicitly selecting Cloud AI in the UI or `/cloud` in the terminal.
- Python standard library only; no pip packages.

**Important:** this is not a standalone iOS/Android app and does not run the model inside the phone yet. The laptop hosts the model and web app. Internet-anywhere access needs a separately deployed, secured server; this first version deliberately stays on your local network.

## 1. Install the small local model

Install Ollama from https://ollama.com/ on the laptop, then run:

```bat
ollama pull tinyllama
```

TinyLlama is a compact starter model (about 637 MB in the model setup used for this project). It can be weak at complex questions, but it is a practical first model for a 4 GB RAM laptop. Keep other apps closed when possible.

## 2. Install Python

Install Python 3.10+ and enable **Add Python to PATH**. No extra Python packages are needed.

## 3. Start the browser version

Double-click `start_web.bat`. Keep the black terminal window open.

It prints:
- A laptop URL, usually `http://127.0.0.1:8765`
- A Wi-Fi URL, such as `http://192.168.x.x:8765`
- A private access token

Open the laptop URL on the laptop, or the Wi-Fi URL on a phone/tablet connected to the same Wi-Fi. Paste the access token into the page and press Connect.

If Windows Firewall asks, allow Python on **Private networks only**. Do not expose this server to the public internet or configure router port forwarding.

## 4. Terminal version

Double-click `run_smolai.bat` or run:

```bat
py -3 smolai.py
```

Commands: `/local`, `/cloud`, `/clear`, `/help`, `/exit`.

## Privacy

- Local is the default.
- In local mode, prompts go from the browser to the laptop, then to its local Ollama service.
- SmolAI does not silently switch to cloud when local AI fails.
- Cloud mode sends chat messages to the provider configured in the laptop's `.env` file. Cloud API use may cost money and is separate from a ChatGPT subscription.
- The browser session uses a random access token printed in the laptop terminal. Keep it private.
- Do not commit `.env` or publish API keys.

## Troubleshooting

- **Model not found:** run `ollama pull tinyllama`.
- **Laptop works, phone cannot connect:** check both are on the same Wi-Fi; allow Python on Windows Private networks; check the printed Wi-Fi IP.
- **Connection refused:** ensure Ollama is running and the laptop server terminal remains open.
- **Slow responses:** close browser tabs and other apps; 4 GB RAM is limited.
- **Port already in use:** set `SMOLAI_PORT` to another port before starting.

## Roadmap

1. Stable local web + terminal MVP.
2. Better tiny model selector.
3. Installable mobile PWA.
4. Optional direct on-device inference on supported Android / desktop devices.
5. Secure remote hosting for access outside the home Wi-Fi.
