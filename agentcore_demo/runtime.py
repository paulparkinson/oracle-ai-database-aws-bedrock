"""AgentCore Runtime adapter; reuse the demo's bounded read-only operations."""
import json
import os
from pathlib import Path
import tempfile
import threading
import time

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from rag import app as demo, nl2sql

app = BedrockAgentCoreApp()
_lock = threading.RLock()
_owners = {}
_wallet = None
_configured = False


def configure_database():
    """Cloud credentials come only from an explicitly scoped Secrets Manager secret."""
    global _wallet, _configured
    if _configured:
        return
    if os.getenv("AGENTCORE_DEMO_LOCAL") == "1":
        demo.core.load_dotenv(demo.ROOT / ".env", override=False)
    else:
        arn = os.environ["ORACLE_SECRET_ARN"]
        secret = demo.core.boto3.client("secretsmanager").get_secret_value(SecretId=arn)
        config = json.loads(secret["SecretString"])
        if not config["dsn"].startswith("tcps://"):
            raise ValueError("A TCPS EZConnect+ DSN is required.")
        if config["user"].upper() in {"ADMIN", "SYS", "SYSTEM"}:
            raise ValueError("Use a dedicated CREATE SESSION-only demo user.")
        os.environ.update(RAG_DB_DSN=config["dsn"], RAG_DB_USER=config["user"],
                          RAG_DB_PASSWORD=config["password"])
        if config.get("wallet_pem"):
            _wallet = tempfile.TemporaryDirectory(prefix="oracle-agentcore-")
            path = Path(_wallet.name) / "ewallet.pem"
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as handle:
                handle.write(config["wallet_pem"])
            os.environ["RAG_DB_WALLET_DIR"] = _wallet.name
            os.environ["RAG_DB_WALLET_PASSWORD"] = config.get("wallet_password", "")
    _configured = True


def dispatch(payload, session_id):
    if not isinstance(payload, dict) or len(json.dumps(payload)) > 2048:
        raise ValueError("Expected a small JSON object.")
    if not isinstance(session_id, str) or not 33 <= len(session_id) <= 256:
        raise ValueError("A runtime session ID of 33–256 characters is required.")
    operation = payload.get("operation")
    fields = {"rag": {"operation", "question"},
              "nl2sql.generate": {"operation", "question"},
              "nl2sql.execute": {"operation", "receipt"}}
    if operation not in fields or set(payload) != fields[operation]:
        raise ValueError("Unsupported operation or fields.")
    # Serializes in-process receipts, including simultaneous duplicate execution.
    # AgentCore sessions are ephemeral: restart/expiry requires a new review.
    with _lock:
        for receipt in list(_owners):
            if receipt not in nl2sql.PENDING or nl2sql.PENDING[receipt]["expires"] < time.monotonic():
                _owners.pop(receipt, None)
                nl2sql.PENDING.pop(receipt, None)
        if operation == "rag":
            if payload["question"] not in demo.QUESTIONS:
                raise ValueError("Choose one of the four policy questions.")
            configure_database()
            return demo.ask(payload["question"])
        if operation == "nl2sql.generate":
            result = nl2sql.generate(payload["question"])
            if "receipt" in result:
                _owners[result["receipt"]] = session_id
            return result
        receipt = payload["receipt"]
        if not isinstance(receipt, str) or _owners.get(receipt) != session_id:
            raise ValueError("Unknown review receipt for this session.")
        configure_database()
        _owners.pop(receipt)
        return nl2sql.execute(receipt)


@app.entrypoint
def invoke(payload, context):
    try:
        return dispatch(payload, context.session_id)
    except Exception:
        # Do not leak Oracle endpoints, secrets, SDK errors or request bodies.
        return {"error": "Request failed validation or a dependency is unavailable. No fallback result was used."}


if __name__ == "__main__":
    if os.getenv("AGENTCORE_DEMO_LOCAL") == "1":
        demo.core.load_dotenv(demo.ROOT / ".env", override=False)
        app.run(host="127.0.0.1", port=8080)
    else:
        app.run()

