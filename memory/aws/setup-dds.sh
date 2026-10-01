#!/usr/bin/env bash
set -euo pipefail
MEMORY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "${MEMORY_DIR}/load-env.sh"
export MEMORY_ADMIN_ENV_FILE="${MEMORY_ADMIN_ENV_FILE:-${MEMORY_DIR}/../.env}"
exec "${MEMORY_DIR}/.venv/bin/python" - <<'PY'
import os, runpy
from pathlib import Path
from dotenv import dotenv_values
config = dotenv_values(os.environ['MEMORY_ADMIN_ENV_FILE'])
os.environ['DDS_ADMIN_PASSWORD'] = config.get('DB_ADMIN_PASSWORD') or config['DB_PASSWORD']
runpy.run_path(str(Path(os.environ['MEMORY_CONFIG_DIR']) / 'deep-data-security/bootstrap.py'), run_name='__main__')
PY
