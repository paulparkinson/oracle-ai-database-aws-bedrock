#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LIBRARY_DIR="${OAM_LIBRARY_DIR:-/Users/pparkins/src/orahub/aire-dev/memory/java/ojdbc-agent-memory}"
if [[ -z "${JAVA_HOME:-}" && -x /usr/libexec/java_home ]]; then
  export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
fi
MAVEN_BIN="${MAVEN_BIN:-mvn}"
if ! command -v "${MAVEN_BIN}" >/dev/null && [[ -x /opt/homebrew/bin/mvn ]]; then
  MAVEN_BIN=/opt/homebrew/bin/mvn
fi
[[ -f "${LIBRARY_DIR}/pom.xml" ]] || { echo "Set OAM_LIBRARY_DIR to the ojdbc-agent-memory source clone." >&2; exit 1; }
"${MAVEN_BIN}" -q -f "${LIBRARY_DIR}/pom.xml" -DskipTests install
"${MAVEN_BIN}" -f "${APP_DIR}/server/pom.xml" clean package
