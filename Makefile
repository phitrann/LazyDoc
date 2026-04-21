SHELL := /bin/bash

.DEFAULT_GOAL := help

.PHONY: help install install-backend install-frontend backend frontend dev test test-backend build-frontend start-frontend clean

help:
	@echo "Available targets:"
	@echo "  install           Install backend and frontend dependencies"
	@echo "  install-backend   Install backend dependencies"
	@echo "  install-frontend  Install frontend dependencies"
	@echo "  backend           Run FastAPI backend on :8992"
	@echo "  frontend          Run Next.js frontend on :3000"
	@echo "  dev               Run backend and frontend together"
	@echo "  test              Run backend tests"
	@echo "  test-backend      Run backend tests"
	@echo "  build-frontend    Build frontend for production"
	@echo "  start-frontend    Start frontend in production mode"
	@echo "  clean             Remove frontend build artifacts"

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

backend:
	cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8992

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend (:8992) and frontend (Next.js dev)..."
	@set -e; \
	( cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8992 ) & \
	BACKEND_PID=$$!; \
	trap 'kill $$BACKEND_PID 2>/dev/null || true' EXIT INT TERM; \
	cd frontend && npm run dev

test: test-backend

test-backend:
	pytest

build-frontend:
	cd frontend && npm run build

start-frontend:
	cd frontend && npm run start

clean:
	cd frontend && rm -rf .next
