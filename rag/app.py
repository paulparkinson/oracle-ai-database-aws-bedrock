#!/usr/bin/env python3
"""Loopback-only live Oracle/Bedrock RAG demo; synthetic documents, read-only SQL."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import rag_smoke_test as core
from rag import nl2sql

QUESTIONS = [core.QUESTION,
    "For Project Cedar, how long is the warranty for replacement sensors?",
    "On which day are Project Maple recycling collections?",
    "What is the approved transfer policy for Project Aspen?"]

def ask(question):
    if question not in QUESTIONS:
        raise ValueError("Choose one of the four demo questions.")
    session = core.boto3.Session(region_name=os.getenv("RAG_AWS_REGION", "us-east-1"))
    config = core.Config(connect_timeout=10, read_timeout=60,
                         retries={"total_max_attempts": 2, "mode": "standard"})
    identity = session.client("sts", config=config).get_caller_identity()
    if identity["Account"] != os.getenv("RAG_EXPECTED_AWS_ACCOUNT", "054037143469"):
        raise ValueError("AWS account guard rejected this session.")
    runtime = session.client("bedrock-runtime", config=config)
    with core.oracledb.connect(**core.connection_options()) as connection:
        connection.call_timeout = 30000
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT SYS_CONTEXT('USERENV','DB_NAME'), SYS_CONTEXT('USERENV','SERVICE_NAME') FROM dual")
            target = " ".join(cursor.fetchone()).lower()
            if os.getenv("RAG_EXPECTED_DB_NAME", "paulparkdbaws").lower() not in target:
                raise ValueError("Oracle database guard rejected this session.")
            model = os.getenv("RAG_EMBED_MODEL", "amazon.titan-embed-text-v2:0")
            docs = [dict(d, embedding=list(core.embed(runtime, model, d["text"]))) for d in core.DOCUMENTS]
            vector = core.embed(runtime, model, question)
            # A temporary LOB locator handles the >32KB JSON embedding payload.
            lob = connection.createlob(core.oracledb.DB_TYPE_CLOB)
            lob.write(json.dumps(docs))
            cursor.setinputsizes(query_vector=core.oracledb.DB_TYPE_VECTOR)
            cursor.execute(core.RETRIEVAL_SQL, documents=lob, query_vector=vector)
            rows = cursor.fetchall()
            if len(rows) != 2 or not all(math.isfinite(float(row[2])) for row in rows):
                raise ValueError("Oracle returned invalid retrieval results.")
            evidence = [{"id": row[0], "text": row[1], "distance": float(row[2])} for row in rows]
        answer = core.generate(runtime, os.getenv("RAG_TEXT_MODEL", "amazon.nova-lite-v1:0"), question, evidence)
    return {"question": question, "answer": answer, "evidence": evidence,
            "verification": "Live Bedrock embeddings → live Oracle VECTOR_DISTANCE → live Bedrock answer",
            "scope": "Three synthetic fixture documents; no business data, persistent writes, or workload-identity claim."}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Avoid logging prompts, credentials and account metadata.

    def send(self, status, body, kind):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, b"Invalid host", "text/plain")
        routes = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript" )}
        if self.path not in routes:
            return self.send(404, b"Not found", "text/plain")
        filename, kind = routes[self.path]
        self.send(200, Path(__file__).with_name(filename).read_bytes(), kind)

    def do_POST(self):
        expected = f"http://127.0.0.1:{self.server.server_port}"
        if not self.valid_host() or self.path not in ("/ask", "/nl2sql/generate", "/nl2sql/execute") or self.headers.get("Origin") != expected:
            return self.send(403, b"Invalid origin", "text/plain")
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 2048:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            if self.path == "/ask":
                result = ask(payload["question"])
            elif self.path == "/nl2sql/generate":
                result = nl2sql.generate(payload["question"])
            else:
                result = nl2sql.execute(payload["receipt"])
            self.send(200, json.dumps(result).encode(), "application/json")
        except ValueError as exc:
            self.send(400, json.dumps({"error": str(exc)}).encode(), "application/json")
        except Exception as exc:
            # Never return raw AWS/Oracle errors that can contain internal identifiers.
            code = type(exc).__name__
            self.send(500, json.dumps({"error": f"Live request failed ({code}). Check the local AWS session and database configuration."}).encode(), "application/json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--port", type=int, default=8095)
    args = parser.parse_args()
    core.load_dotenv(args.env_file, override=False)
    print(f"Open http://127.0.0.1:{args.port} — live calls incur Bedrock charges.", flush=True)
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
