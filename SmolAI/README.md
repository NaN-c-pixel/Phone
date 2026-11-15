# SmolAI

A lightweight terminal AI assistant for Windows.

- **Local AI:** Ollama running on your laptop.
- **Optional cloud AI:** an OpenAI-compatible Chat Completions API.
- **Privacy default:** starts local and never silently falls back to cloud.

## Hardware note

The Dell Vostro 3558 with 4 GB RAM is a tight fit for local AI. Start with
TinyLlama, close unnecessary apps, and expect slower responses. A compatible
RAM upgrade can help; verify the exact memory specifications before buying.

## 1. Install Python

Install Python 3.10 or newer for Windows. Enable **Add Python to PATH**.
SmolAI uses only Python's standard library; no pip packages are required.

## 2. Install Ollama

Install Ollama for Windows from https://ollama.com/

Open Command Prompt and run:

```bat
ollama pull tinyllama
ollama run tinyllama
```

When the model responds, type `/bye` to exit. Ollama normally exposes its
local API at `http://127.0.0.1:11434`.

## 3. Configure SmolAI

Copy `.env.example` to a file named `.env` in this folder. The defaults
select TinyLlama. You do not need a cloud key for local mode.

## 4. Start SmolAI

Double-click `run_smolai.bat`, or run:

```bat
py -3 smolai.py
```

Try asking: `Hi SmolAI, introduce yourself.`

## Commands

| Command | Action |
|---|---|
| `/local` | Use local Ollama |
| `/cloud` | Use configured cloud API |
| `/clear` | Clear chat history |
| `/help` | Show commands |
| `/exit` | Quit |

## Hybrid mode and privacy

SmolAI starts in local mode. It does not automatically upload prompts when
Ollama is unavailable. You must explicitly type `/cloud` to use the cloud
provider. Cloud requests send conversation context to that provider.

Cloud API access is separate from a ChatGPT subscription and may incur
charges. Have the account owner choose the provider, review its privacy
terms and pricing, and approve any API account or payment setup. Never
commit `.env` or publish an API key.

## Troubleshooting

- **Connection refused:** make sure Ollama is running.
- **Model not found:** run `ollama pull tinyllama`.
- **Slow / out of memory:** close browsers and other apps; stay with TinyLlama.
- **Python not found:** reinstall Python and enable PATH, or try `py -3`.

## Roadmap

1. Terminal chat MVP.
2. Model picker and local conversation history.
3. Optional voice input and speech output.
4. Local document search.
5. Permission-based desktop automation.
