# Flynn's Theme Park memory app on AWS

Verification on October 1, 2026: both apps passed their complete API smoke tests
from the workstation against the live `THEMEPARK` schema on `paulparkdbaws`.
Java build/unit checks and six Python unit tests passed. Installation on the
AWS instance is pending its connection details; the DDS end-user/data-grant
setup is pending explicit access-change approval. DDS is not yet verified.

The app shown in `memory-app-45sec-scroll-through.mov` is
[`memory/java-agent`](memory/java-agent/README.md), with live conversation
extraction, semantic recall, memory lifecycle, Memory Quest, and a database
inspector. The companion [`memory/python-agent`](memory/python-agent/README.md)
adds the public Python SDK, Deep Data Security proof, lakehouse telemetry, and
the consent-scoped AR simulator. Deploy both to run the complete set of demos.

## Prepare once

The target is Oracle Database@AWS `paulparkdbaws`. The private root `.env`
contains its ADMIN connection and wallet configuration. From the repository root:

```bash
python3.12 -m venv memory/.venv
memory/.venv/bin/python -m pip install -r memory/python-agent/requirements.txt
memory/.venv/bin/python memory/aws/setup-database.py
```

Setup verifies the database identity, creates the dedicated `THEMEPARK` demo
schema, saves generated application/end-user passwords to ignored `memory/.env`
with mode `0600`, and imports `ALLMINILM` (384 dimensions). Reruns reuse credentials
and the existing model; they do not reset passwords or drop data. Demo tables are
initialized by the Java app's `--setup-db` mode. The SDK initializes `MAGIC_PY_*`
when Python starts. The model loader uses a client-side download and BLOB import;
it does not grant the app `DBMS_CLOUD` access.

On the build workstation, provide Java 21+ and Maven, and set `OAM_LIBRARY_DIR`
to the existing `ojdbc-agent-memory` source clone. It is an external library
dependency, not included as source in this public repository. The private
deployment bundle contains the compiled app and library; do not publish it as
a public release without reviewing that library's distribution terms.

On the existing Linux AWS instance, provide Java 21+, Python 3.12 with venv,
`curl`, `tar`, systemd, sudo access, and a running Ollama service:

```bash
ollama pull llama3.2
```

Use the [Ollama Linux installation instructions](https://docs.ollama.com/linux)
if Ollama is absent. The instance must reach the database listener through the
configured network path, and reach package/model downloads during setup.

## Deploy and open

```bash
# On the workstation; replace the SSH target and key with the existing instance.
export OAM_LIBRARY_DIR=/path/to/ojdbc-agent-memory
memory/aws/deploy-instance.sh ec2-user@INSTANCE /path/to/instance-key.pem
ssh -i /path/to/instance-key.pem \
  -L 8091:127.0.0.1:8091 -L 8092:127.0.0.1:8092 ec2-user@INSTANCE
```

Open <http://localhost:8091> for the Java app shown in the video, and
<http://localhost:8092> for the Python app. Both run as systemd services and
restart after reboot. The apps stay bound to loopback; the SSH tunnel provides
access without exposing the demo's reset and write controls publicly.

The deployment script builds/tests the Java JAR, transfers a private bundle,
application-only configuration and wallet over SSH, adjusts the wallet path,
initializes the shared demo schema, installs both services, and checks both
database health endpoints. ADMIN credentials are excluded from the instance
configuration. It uses the instance's existing login user and sudo permissions.

## Verify and finish Deep Data Security

On the instance, after deployment:

```bash
cd ~/themepark-memory
java-agent/smoke-test.sh
python-agent/smoke-test.sh
```

These smoke tests reset and write synthetic demo rows. They exercise extraction,
recall, correction, TTL, approval/reuse, quest checkpoints and graph/vector
retrieval; Python additionally exercises lakehouse and the AR simulator.

For the database-enforced Ava/Leo panel, initialize DDS once from the workstation
after the Python app has created its managed memory table:

```bash
# Reads the ADMIN password privately from root .env; does not save it in memory/.env.
memory/aws/setup-dds.sh
```

Then refresh the Python panel. It must report `databaseEnforced: true` and
`crossUserProbe.returnedRows: 0`. A `setup-required` response does not constitute a DDS pass.
AR is a browser simulator; Spectacles hardware is unvalidated. Lakehouse data is
a synthetic aggregated fixture, not a live Iceberg ingestion pipeline.

## Restart or inspect

```bash
sudo systemctl restart themepark-java themepark-python
sudo systemctl status themepark-java themepark-python
sudo journalctl -u themepark-java -u themepark-python -n 50
```

Update code by rerunning `deploy-instance.sh`; it restarts both services.
Credentials, wallets, `.venv`, `.runtime`, JARs and Maven build output stay out
of Git. Treat `.runtime/instance.env` and `instance-wallet.tar.gz` as private
secrets. The separate Bedrock RAG test remains documented in [README.md](README.md);
the memory browser uses Oracle and Ollama and does not invoke Bedrock.

Model import reference: [Oracle DBMS_VECTOR.LOAD_ONNX_MODEL](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/load_onnx_model-procedure.html).
