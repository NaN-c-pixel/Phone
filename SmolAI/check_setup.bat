@echo off
title SmolAI Setup Check
echo === Python ===
py -3 --version
echo.
echo === Ollama executable ===
where ollama
echo.
echo === Installed local models ===
ollama list
echo.
echo If TinyLlama is missing, run: ollama pull tinyllama
pause
