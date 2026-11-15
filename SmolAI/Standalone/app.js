import { pipeline, env } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.0";

const MODEL = "onnx-community/Qwen2.5-0.5B-Instruct";
const $ = (id) => document.getElementById(id);
let generator = null;
let busy = false;
let history = [];

env.allowLocalModels = false;
env.allowRemoteModels = true;
env.useBrowserCache = true;
if (env.backends?.onnx?.wasm) {
  env.backends.onnx.wasm.numThreads = 1;
}

function status(message) { $("statusText").textContent = message; }
function progress(value) { $("bar").style.width = Math.max(0, Math.min(100, value)) + "%"; }
function addMessage(role, content) {
  const node = document.createElement("div");
  node.className = "msg " + (role === "user" ? "user" : "assistant");
  node.textContent = content;
  $("chat").appendChild(node);
  node.scrollIntoView({ behavior: "smooth", block: "end" });
}
function setReady(ready) {
  $("prompt").disabled = !ready;
  $("send").disabled = !ready;
  $("load").disabled = ready || busy;
}
function saveHistory() {
  try { localStorage.setItem("smolai-chat-v1", JSON.stringify(history.slice(-16))); } catch {}
}
function loadHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem("smolai-chat-v1") || "[]");
    if (Array.isArray(saved)) {
      history = saved.filter(x => x && ["user","assistant"].includes(x.role) && typeof x.content === "string").slice(-16);
      for (const item of history) addMessage(item.role, item.content);
    }
  } catch {}
}
async function loadModel() {
  if (generator || busy) return;
  busy = true;
  $("load").disabled = true;
  status("Checking device acceleration…");
  try {
    const useGPU = !!navigator.gpu;
    const device = useGPU ? "webgpu" : "wasm";
    const dtype = useGPU ? "q4f16" : "q4";
    $("deviceStatus").textContent = useGPU ? "GPU acceleration" : "CPU mode";
    status("Loading " + MODEL + " (" + dtype + "). The first download can take a few minutes…");
    progress(3);
    const options = {
      progress_callback: (event) => {
        if (event && typeof event.progress === "number") progress(event.progress);
        if (event && event.status) status(event.status + (event.file ? ": " + event.file : ""));
      }
    };
    try {
      generator = await pipeline("text-generation", MODEL, { ...options, device, dtype });
    } catch (gpuError) {
      if (device !== "webgpu") throw gpuError;
      status("GPU setup failed. Retrying with CPU mode; this may download a larger model file and run more slowly…");
      progress(0);
      $("deviceStatus").textContent = "CPU fallback";
      generator = await pipeline("text-generation", MODEL, { ...options, device: "wasm", dtype: "q4" });
    }
    progress(100);
    status("AI ready. Model loaded on this device. You can now chat offline when its files remain cached.");
    setReady(true);
    $("load").textContent = "AI loaded ✓";
    addMessage("assistant", "My AI brain is ready. Ask me anything!");
  } catch (error) {
    generator = null;
    $("load").disabled = false;
    status("Couldn't load the model: " + (error?.message || String(error)) + ". Check your connection/storage and try again. If GPU mode fails, this browser may not support WebGPU.");
    addMessage("assistant", "Model loading failed. " + (error?.message || String(error)));
  } finally {
    busy = false;
    if (!generator) $("load").disabled = false;
  }
}
async function sendMessage(event) {
  event.preventDefault();
  const text = $("prompt").value.trim();
  if (!text || !generator || busy) return;
  $("prompt").value = "";
  history.push({ role: "user", content: text });
  addMessage("user", text);
  busy = true;
  $("send").disabled = true;
  try {
    const messages = [
      { role: "system", content: "You are SmolAI, a helpful, friendly and concise assistant. Reply in the language the user uses. Be honest when unsure. You are a small on-device model and should not pretend to know things you do not know." },
      ...history.slice(-8)
    ];
    const output = await generator(messages, {
      max_new_tokens: 180,
      do_sample: false,
      repetition_penalty: 1.08
    });
    const generated = output?.[0]?.generated_text;
    const last = Array.isArray(generated) ? generated[generated.length - 1] : null;
    const answer = typeof last === "string" ? last : (last?.content || "");
    const clean = String(answer).trim() || "I couldn't generate a reply. Try a shorter message.";
    history.push({ role: "assistant", content: clean });
    history = history.slice(-16);
    saveHistory();
    addMessage("assistant", clean);
  } catch (error) {
    history.pop();
    addMessage("assistant", "Generation error: " + (error?.message || String(error)));
  } finally {
    busy = false;
    $("send").disabled = !generator;
    $("prompt").focus();
  }
}
$("load").addEventListener("click", loadModel);
$("form").addEventListener("submit", sendMessage);
loadHistory();
if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}
if (navigator.storage?.persist) navigator.storage.persist().catch(() => {});
$("deviceStatus").textContent = navigator.gpu ? "WebGPU available" : "CPU fallback";
let installPrompt = null;
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  $("install").style.display = "inline-block";
});
$("install").addEventListener("click", async () => {
  if (!installPrompt) {
    alert("On iPhone/iPad: open this page in Safari, tap Share, then Add to Home Screen.");
    return;
  }
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = null;
  $("install").style.display = "none";
});
if (/iphone|ipad|ipod/i.test(navigator.userAgent)) {
  $("install").style.display = "inline-block";
}
