# SmolAI Standalone

This is the standalone, on-device version of SmolAI. It does **not** connect to your Dell, Ollama, or a SmolAI server.

## What it does

- Installs like an app (PWA) on supported phones, tablets and computers.
- Runs a small language model inside the device's browser using Transformers.js.
- Stores chat history on the device.
- No API key, cloud account, or backend server.
- First-time model download is required; the browser needs internet for the initial app/library/model download.

## Model

Default: `onnx-community/Qwen2.5-0.5B-Instruct`, a 0.5-billion-parameter instruction model with Vietnamese and other language support. It uses a quantized model file: roughly 483 MB for Q4F16 on WebGPU or 786 MB for Q4 on CPU. Model quality is limited compared with larger assistants.

Model card: https://huggingface.co/onnx-community/Qwen2.5-0.5B-Instruct

## Install

The app must be served from HTTPS for PWA installation and service workers. Publish this folder with GitHub Pages or another static HTTPS host.

- **Windows / macOS / Linux:** open the HTTPS page in a supported browser and use its Install app option.
- **Android:** open in Chrome, then use Install app / Add to Home screen.
- **iPhone / iPad:** open in Safari, tap Share, then Add to Home Screen.

## First run

1. Open SmolAI Standalone.
2. Tap **Download & load AI model**.
3. Wait for the model download and setup to finish.
4. Start chatting. The model runs on the device.

After the first download, the app shell is cached and Transformers.js stores model files in browser cache. Offline use depends on the browser retaining those cached files; the browser may clear them under storage pressure. Keep enough free storage.

## Device requirements and limitations

- WebGPU is used when available; otherwise the app tries CPU/WASM.
- Current Transformers.js releases support WebGPU on recent browsers; Safari support depends on OS version. If WebGPU is missing, CPU fallback may be much slower.
- Phones with limited memory may fail to load the model. Close other apps and retry.
- The existing Dell with 4 GB RAM may be too constrained for browser inference, especially while Windows is running. This is not a promise that every device can run it.
- iOS does not allow arbitrary desktop-style executable installers. The PWA is the cross-platform standalone route.
- This app has no internet search, file access, voice, or cloud fallback yet.

## Privacy

Chat inference is local. The model and app library are downloaded from their publishers during setup. After setup, prompts are processed on the device and are not sent to a chat API. Do not add sensitive information to a small experimental model.

## Development

Files:
- `index.html` — app interface
- `app.js` — local model loading and chat
- `sw.js` — offline app-shell cache
- `manifest.webmanifest` — installable PWA metadata
- `icon.svg` — app icon
