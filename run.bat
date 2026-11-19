@echo off
cd /d "%~dp0"
echo Starting EcoTracker Platform...
uv run python -m app.dashboard
