@echo off
title SmolAI Web
cd /d "%~dp0"
py -3 web_server.py
if errorlevel 1 (
  echo.
  echo SmolAI Web stopped. Check README.md.
  pause
)
