#!/usr/bin/env bash
# Run as the instance login user from the extracted memory directory.
set -euo pipefail
MEMORY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "${MEMORY_DIR}" != *' '* ]] || { echo "Use an install path without spaces." >&2; exit 1; }
source "${MEMORY_DIR}/load-env.sh"
JAVA_BIN="${JAVA_HOME:+${JAVA_HOME}/bin/}java"
command -v "${JAVA_BIN}" >/dev/null || { echo "Install Java 21+ first." >&2; exit 1; }
JAVA_MAJOR="$("${JAVA_BIN}" -version 2>&1 | sed -n 's/.*version "\([0-9]*\).*/\1/p' | head -1)"
[[ "${JAVA_MAJOR}" =~ ^[0-9]+$ && "${JAVA_MAJOR}" -ge 21 ]] || { echo "Java 21+ is required." >&2; exit 1; }
command -v curl >/dev/null
command -v systemctl >/dev/null
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
if ! command -v "${PYTHON_BIN}" >/dev/null; then PYTHON_BIN=python3; fi
"${PYTHON_BIN}" -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ is required; use 3.12"'
curl -fsS "${OLLAMA_BASE_URL:-http://127.0.0.1:11434}/api/tags" | \
  "${PYTHON_BIN}" -c 'import json,sys,os; models=json.load(sys.stdin)["models"]; wanted=os.getenv("OLLAMA_MODEL","llama3.2:latest"); assert any(m["name"]==wanted for m in models), "Pull the configured Ollama model first"'
[[ -f "${MEMORY_DIR}/java-agent/server/target/memories-are-the-magic-0.1.0-SNAPSHOT.jar" ]] || { echo "Extract the bundle made by aws/package.sh first." >&2; exit 1; }
chmod 600 "${MEMORY_ENV_FILE:?Configure memory/.env first.}"
"${PYTHON_BIN}" -m venv "${MEMORY_DIR}/.venv"
"${MEMORY_DIR}/.venv/bin/python" -m pip install -q -r "${MEMORY_DIR}/python-agent/requirements.txt"
"${MEMORY_DIR}/java-agent/run.sh" --setup-db
for lane in java python; do
  unit="$(mktemp)"
  cat > "${unit}" <<EOF
[Unit]
Description=Flynn's Theme Park ${lane} memory demo
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
User=$(id -un)
WorkingDirectory=${MEMORY_DIR}
Environment=MEMORY_ENV_FILE=${MEMORY_ENV_FILE}
Environment=MEMORY_SKIP_INSTALL=1
Environment=JAVA_HOME=${JAVA_HOME:-}
ExecStart=/bin/bash ${MEMORY_DIR}/${lane}-agent/run.sh
Restart=on-failure
RestartSec=5
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF
  sudo install -m 644 "${unit}" "/etc/systemd/system/themepark-${lane}.service"
  rm -f "${unit}"
done
sudo systemctl daemon-reload
sudo systemctl enable themepark-java themepark-python
sudo systemctl restart themepark-java themepark-python
for port in "${MEMORY_PORT}" "${MEMORY_PYTHON_PORT}"; do
  curl --retry 30 --retry-connrefused --retry-delay 2 -fsS "http://127.0.0.1:${port}/api/health"
done
echo "Both apps are running. Forward ports 8091 and 8092 over SSH to open them."
