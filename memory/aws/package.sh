#!/usr/bin/env bash
# Build a private deployment artifact with both UIs, no credentials or wallets.
set -euo pipefail
MEMORY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${MEMORY_DIR}/java-agent/build.sh"
mkdir -p "${MEMORY_DIR}/.runtime"
tar -czf "${MEMORY_DIR}/.runtime/memory-app.tar.gz" \
  --exclude=__pycache__ --exclude='*.pyc' \
  -C "${MEMORY_DIR}" load-env.sh run.sh test.sh smoke-test.sh \
  python-agent java-agent/web java-agent/run.sh java-agent/load-database-env.sh \
  java-agent/server/target/memories-are-the-magic-0.1.0-SNAPSHOT.jar \
  aws/install-instance.sh deep-data-security test-utils/src/main/java/com/oracle/ojdbc/agentmemory/examples/AllMiniLmInstaller.java
echo "Private deployment bundle: memory/.runtime/memory-app.tar.gz"
