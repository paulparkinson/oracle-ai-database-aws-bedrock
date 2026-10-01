#!/usr/bin/env bash
set -euo pipefail
PYTHON_APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MEMORY_DIR="$(cd -- "${PYTHON_APP_DIR}/.." && pwd)"
source "${MEMORY_DIR}/load-env.sh"
VENV_DIR="${MEMORY_DIR}/.venv"
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi
if [[ "${MEMORY_SKIP_INSTALL:-0}" != 1 ]]; then
  "${VENV_DIR}/bin/python" -m pip install -q -r "${PYTHON_APP_DIR}/requirements.txt"
fi
exec "${VENV_DIR}/bin/python" "${PYTHON_APP_DIR}/app.py"
