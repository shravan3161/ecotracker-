@echo off
cd /d "%~dp0frontend"
echo Starting Vite React Dev Server at http://localhost:5173 (proxying API to localhost:8085)...
npm.cmd run dev
