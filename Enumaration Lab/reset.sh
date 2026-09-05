#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false

if command -v docker >/dev/null 2>&1; then
  v="$(docker --version 2>&1 || true)"
  if printf '%s' "$v" | grep -qi 'podman\|Emulate Docker CLI'; then
    if command -v podman >/dev/null 2>&1; then
      mkdir -p /run/podman
      [ -S /run/podman/podman.sock ] || nohup podman system service --time=0 unix:///run/podman/podman.sock >/tmp/ithlab-podman-service.log 2>&1 &
      for _ in $(seq 1 20); do [ -S /run/podman/podman.sock ] && break; sleep .5; done
      export DOCKER_HOST=unix:///run/podman/podman.sock
    fi
  fi
  docker compose down -v || true
elif command -v podman-compose >/dev/null 2>&1; then
  podman-compose down -v || true
fi
printf '%s\n' 'ImranTheExploitHunter lab reset. Run ./start.sh again.'
