@echo off
title SmolAI
cd /d "%~dp0"
py -3 smolai.py
if errorlevel 1 (
  echo.
  echo SmolAI stopped. Check README.md for setup help.
  pause
)
