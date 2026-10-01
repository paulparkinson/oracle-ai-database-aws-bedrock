#!/usr/bin/env bash
# Deploy the private bundle, application credentials and wallet over SSH.
set -euo pipefail
TARGET="${1:?Usage: deploy-instance.sh user@host [ssh-key-path]}"
[[ "${TARGET}" =~ ^[a-zA-Z0-9_.@:-]+$ && "${TARGET}" != -* ]] || exit 1
MEMORY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "${MEMORY_DIR}/load-env.sh"
SSH_OPTIONS=(-o StrictHostKeyChecking=accept-new)
if [[ -n "${2:-}" ]]; then SSH_OPTIONS+=(-i "$2"); fi
REMOTE_HOME="$(ssh "${SSH_OPTIONS[@]}" "${TARGET}" 'printf "%s" "$HOME"')"
[[ "${REMOTE_HOME}" =~ ^/[a-zA-Z0-9_/-]+$ ]] || { echo "Unsupported remote home path." >&2; exit 1; }
REMOTE_DIR="${REMOTE_HOME}/themepark-memory"
"${MEMORY_DIR}/aws/package.sh"
MEMORY_REMOTE_DIR="${REMOTE_DIR}" "${MEMORY_DIR}/.venv/bin/python" - <<'PY'
import os, shlex
from pathlib import Path
from dotenv import dotenv_values
config = dict(dotenv_values(os.environ['MEMORY_ENV_FILE']))
config['TNS_ADMIN'] = os.environ['MEMORY_REMOTE_DIR'] + '/wallet'
config.pop('DB_URL', None)
# Only application configuration goes to the instance, never an ADMIN password.
allowed = {'DB_USERNAME','DB_PASSWORD','DB_SERVICE','TNS_ADMIN','DB_WALLET_PASSWORD',
           'DDS_AVA_PASSWORD','DDS_LEO_PASSWORD','MEMORY_PORT','MEMORY_PYTHON_PORT',
           'OLLAMA_MODEL','OLLAMA_BASE_URL','AR_ALLOWED_ORIGIN'}
target = Path(os.environ['MEMORY_CONFIG_DIR']) / '.runtime/instance.env'
with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as stream:
    for key, value in config.items():
        if key in allowed and value is not None:
            stream.write(f'{key}={shlex.quote(value)}\n')
PY
tar -czf "${MEMORY_DIR}/.runtime/instance-wallet.tar.gz" -C "${TNS_ADMIN}" .
chmod 600 "${MEMORY_DIR}/.runtime/instance-wallet.tar.gz"
ssh "${SSH_OPTIONS[@]}" "${TARGET}" "umask 077; mkdir -p '${REMOTE_DIR}/wallet'"
scp "${SSH_OPTIONS[@]}" "${MEMORY_DIR}/.runtime/memory-app.tar.gz" "${MEMORY_DIR}/.runtime/instance-wallet.tar.gz" "${TARGET}:${REMOTE_DIR}/"
scp "${SSH_OPTIONS[@]}" "${MEMORY_DIR}/.runtime/instance.env" "${TARGET}:${REMOTE_DIR}/.env"
ssh "${SSH_OPTIONS[@]}" "${TARGET}" "cd '${REMOTE_DIR}' && tar -xzf memory-app.tar.gz && tar -xzf instance-wallet.tar.gz -C wallet && bash aws/install-instance.sh"
echo "Open a tunnel: ssh -L 8091:127.0.0.1:8091 -L 8092:127.0.0.1:8092 ${TARGET}"
