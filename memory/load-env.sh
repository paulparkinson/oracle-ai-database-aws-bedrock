#!/usr/bin/env bash
# Shared configuration for Linux, macOS, and systemd. Source this file.
MEMORY_CONFIG_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export MEMORY_CONFIG_DIR
if [[ -n "${MEMORY_ENV_FILE:-}" ]]; then
  export MEMORY_ENV_FILE
  [[ -f "${MEMORY_ENV_FILE}" ]] || { echo "Missing MEMORY_ENV_FILE." >&2; return 1; }
elif [[ -f "${MEMORY_CONFIG_DIR}/.env" ]]; then
  MEMORY_ENV_FILE="${MEMORY_CONFIG_DIR}/.env"
elif [[ -f "${MEMORY_CONFIG_DIR}/../financial/setup/.env" ]]; then
  MEMORY_ENV_FILE="${MEMORY_CONFIG_DIR}/../financial/setup/.env"
fi
if [[ -n "${MEMORY_ENV_FILE:-}" ]]; then
  set -a
  export MEMORY_ENV_FILE
  # shellcheck disable=SC1090
  source "${MEMORY_ENV_FILE}"
  set +a
fi
export DB_USERNAME="${DB_USERNAME:-${DB_USER:-}}"
export DB_SERVICE="${DB_SERVICE:-${RAG_DB_DSN:-}}"
export TNS_ADMIN="${TNS_ADMIN:-${DB_WALLET_DIR:-${WALLET_DIR:-}}}"
export DB_WALLET_PASSWORD="${DB_WALLET_PASSWORD:-${WALLET_PASSWORD:-${DB_PASSWORD:-}}}"
export MEMORY_PORT="${MEMORY_PORT:-8091}"
export MEMORY_PYTHON_PORT="${MEMORY_PYTHON_PORT:-8092}"
: "${DB_USERNAME:?Set DB_USERNAME in memory/.env or MEMORY_ENV_FILE.}"
: "${DB_SERVICE:?Set DB_SERVICE to the target wallet alias.}"
: "${DB_PASSWORD:?Set DB_PASSWORD.}"
: "${TNS_ADMIN:?Set TNS_ADMIN to the extracted target wallet.}"
[[ -f "${TNS_ADMIN}/tnsnames.ora" ]] || { echo "Wallet tnsnames.ora is missing." >&2; return 1; }
export DB_URL="${DB_URL:-jdbc:oracle:thin:@${DB_SERVICE}?TNS_ADMIN=${TNS_ADMIN}}"
