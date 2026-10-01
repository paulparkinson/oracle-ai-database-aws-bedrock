#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${APP_DIR}/load-database-env.sh"
if [[ -z "${JAVA_HOME:-}" && -x /usr/libexec/java_home ]]; then
  export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
fi
JAVA_BIN="${JAVA_HOME:+${JAVA_HOME}/bin/}java"
APP_JAR="${APP_DIR}/server/target/memories-are-the-magic-0.1.0-SNAPSHOT.jar"
if [[ ! -f "${APP_JAR}" || "${MEMORY_REBUILD:-0}" == 1 ]]; then
  "${APP_DIR}/build.sh"
fi
export MEMORY_WEB_ROOT="${APP_DIR}/web"
exec "${JAVA_BIN}" -jar "${APP_JAR}" "$@"
