#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export COMPOSE_BAKE=false
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

log(){ printf '%s\n' "$*"; }
die(){ printf '[!] %s\n' "$*" >&2; exit 1; }

# Detect the actual container engine. Kali commonly provides Docker CLI as a Podman wrapper.
engine=""
if command -v docker >/dev/null 2>&1; then
  dv="$(docker --version 2>&1 || true)"
  if printf '%s' "$dv" | grep -qi 'podman\|Emulate Docker CLI'; then
    engine="podman"
  elif docker info >/dev/null 2>&1; then
    engine="docker"
  fi
fi
[ -n "$engine" ] || { command -v podman >/dev/null 2>&1 && engine="podman"; }
[ -n "$engine" ] || die 'Docker Engine or Podman is required.'

cleanup_podman(){
  log '[+] Removing previous ImranTheExploitHunter lab runtime...'
  # Only remove containers/networks/volumes belonging to this lab. Never touch unrelated containers.
  for n in v7-api-1 v7-web-1 v8-api-1 v8-web-1 ithlab-api ithlab-web ith-oscp-target ith-oscp-dns; do
    podman rm -f "$n" >/dev/null 2>&1 || true
  done
  for n in ith-oscp-lab v7_control v8_control ithlab-v5_control; do
    podman network rm "$n" >/dev/null 2>&1 || true
  done
  for n in v7_labdata v8_labdata ithlab-v5_labdata; do
    podman volume rm -f "$n" >/dev/null 2>&1 || true
  done
  # Remove only our old tagged images so every build starts clean.
  for img in imrantheexploithunter-api:5.0 imrantheexploithunter-target:5.0 imrantheexploithunter-dns:5.0; do
    podman rmi -f "$img" >/dev/null 2>&1 || true
  done
}

build_images(){
  log '[+] Building all lab images from scratch...'
  # BuildKit/Bake disabled above for predictable Podman compatibility.
  $compose build --no-cache api dns target
}

if [ "$engine" = "docker" ]; then
  log '[+] Real Docker Engine detected.'
  compose='docker compose'
  export CONTAINER_SOCK="${CONTAINER_SOCK:-/var/run/docker.sock}"
  $compose version >/dev/null 2>&1 || die 'Docker Compose is unavailable.'

  log '[+] Cleaning previous lab runtime...'
  for n in v7-api-1 v7-web-1 v8-api-1 v8-web-1 ith-oscp-target ith-oscp-dns; do docker rm -f "$n" >/dev/null 2>&1 || true; done
  for n in ith-oscp-lab v7_control v8_control; do docker network rm "$n" >/dev/null 2>&1 || true; done
  for n in v7_labdata v8_labdata; do docker volume rm -f "$n" >/dev/null 2>&1 || true; done

  compose='docker compose'
  build_images
  log '[+] Starting controller + web...'
  $compose up -d api web
  log '[+] Waiting for API...'
  for _ in $(seq 1 40); do
    if curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then break; fi
    sleep 1
  done
  curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1 || die 'API did not become ready.'
  curl -fsS -X POST http://127.0.0.1:8080/api/lab/start >/dev/null || die 'Lab provisioning failed.'
else
  log '[+] Podman detected. Using Podman directly for controller startup (avoids Compose/conmon startup race).'
  command -v podman >/dev/null 2>&1 || die 'Podman is required.'
  cleanup_podman

  # Start the Podman API socket for the FastAPI controller's Docker SDK.
  if [ "$(id -u)" -eq 0 ]; then
    socket=/run/podman/podman.sock
    mkdir -p /run/podman
    pkill -f 'podman system service.*podman.sock' >/dev/null 2>&1 || true
    nohup podman system service --time=0 "unix://$socket" >/tmp/ithlab-podman-service.log 2>&1 &
    for _ in $(seq 1 40); do [ -S "$socket" ] && break; sleep .25; done
  else
    socket="${XDG_RUNTIME_DIR}/podman/podman.sock"
    systemctl --user enable --now podman.socket >/dev/null 2>&1 || true
  fi
  [ -S "$socket" ] || die "Podman API socket unavailable: $socket"
  export DOCKER_HOST="unix://$socket"
  export CONTAINER_SOCK="$socket"

  if command -v podman-compose >/dev/null 2>&1; then
    compose='podman-compose'
  elif command -v docker-compose >/dev/null 2>&1; then
    compose='docker-compose'
  else
    compose='docker compose'
  fi
  $compose version >/dev/null 2>&1 || die 'Compose is unavailable for image building.'

  build_images

  log '[+] Creating clean controller network...'
  podman network create --driver bridge v7_control >/dev/null
  podman volume create v7_labdata >/dev/null

  log '[+] Starting API controller directly...'
  podman run -d --name ithlab-api \
    --network v7_control --network-alias api \
    --restart unless-stopped \
    -e DATA_DIR=/data \
    -e LAB_SUBNET=172.31.77.0/24 \
    -e TARGET_IMAGE=imrantheexploithunter-target:5.0 \
    -e DNS_IMAGE=imrantheexploithunter-dns:5.0 \
    -v v7_labdata:/data \
    -v "$socket:/var/run/docker.sock" \
    imrantheexploithunter-api:5.0 \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null

  log '[+] Starting web frontend directly...'
  podman run -d --name ithlab-web \
    --network v7_control \
    --restart unless-stopped \
    -p 127.0.0.1:8080:80 \
    -v "$PWD/frontend:/usr/share/nginx/html:ro" \
    -v "$PWD/frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
    nginx:alpine >/dev/null

  log '[+] Waiting for controller...'
  ready=0
  for _ in $(seq 1 40); do
    if curl -fsS http://127.0.0.1:8080/api/health >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  [ "$ready" -eq 1 ] || {
    podman logs ithlab-api --tail 100 >&2 || true
    die 'API did not become ready.'
  }

  log '[+] Provisioning target + DNS automatically...'
  curl -fsS -X POST http://127.0.0.1:8080/api/lab/start >/dev/null || {
    podman logs ithlab-api --tail 100 >&2 || true
    die 'Lab provisioning failed.'
  }
fi

printf '\n==============================================\n'
printf ' ImranTheExploitHunter | OSCP-Style PentestLab\n'
printf '==============================================\n'
printf ' Build : COMPLETE\n'
printf ' Lab   : RUNNING\n'
printf ' Web   : http://127.0.0.1:8080\n'
printf ' Target: 172.31.77.10\n'
printf ' DNS   : 172.31.77.2\n'
printf '==============================================\n\n'
