# Makefile for EcoTracker Agent

.PHONY: install playground run dashboard test

install:
	uv sync

playground:
	uv run adk web app --host 127.0.0.1 --port 18081

dashboard:
	uv run python -m app.dashboard

run:
	uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000

test:
	uv run pytest tests -v
