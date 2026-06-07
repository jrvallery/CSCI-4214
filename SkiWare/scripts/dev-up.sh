#!/usr/bin/env bash
# Idempotent bring-up of the SkiWare local dev stack.
# Safe to call from multiple worktrees — the first one wins the ports;
# subsequent worktrees detect the running stack and skip.
set -euo pipefail

cd "$SUPERCONDUCTOR_ROOT_PATH"

# Fast path: stack already running?
if docker ps --filter "name=skiware-app" --filter "status=running" \
    --format '{{.Names}}' | grep -q skiware-app; then
  echo "SkiWare stack already running — skipping bring-up."
  exit 0
fi

# Docker daemon reachable?
if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not running — start Docker Desktop and retry." >&2
  exit 0
fi

docker compose up --build -d
docker compose exec -T app alembic upgrade head

echo ""
echo "SkiWare stack is up."
echo "  backend:  http://localhost:8080"
echo "  frontend: http://localhost:5173"
