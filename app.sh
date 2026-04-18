#!/bin/sh
set -eu

HOST="0.0.0.0"
INPUT_DIR="${1:-/code/data/classcentral-datacamp-yaml}"

pick_port() {
  for port in 8821 8822 8823; do
    if python - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind(("0.0.0.0", port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
    then
      echo "$port"
      return 0
    fi
  done
  return 1
}

PORT="$(pick_port || true)"

if [ -z "${PORT}" ]; then
  echo "no free port found in 8821, 8822, 8823" >&2
  exit 1
fi

echo "starting web app on http://${HOST}:${PORT}"
exec env PYTHONPATH=/code/src python -m course_pipeline.cli serve-web-app "${INPUT_DIR}" --host "${HOST}" --port "${PORT}"
