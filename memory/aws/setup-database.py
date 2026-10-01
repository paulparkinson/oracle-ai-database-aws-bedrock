#!/usr/bin/env python3
"""Create an isolated demo schema and load ALLMINILM in the verified AWS DB."""
import argparse
import os
from pathlib import Path
import re
import secrets
import shlex
from urllib.request import urlopen

import oracledb
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def connect(config):
    wallet = config.get("TNS_ADMIN") or config["DB_WALLET_DIR"]
    return oracledb.connect(
        user=config["DB_USERNAME"], password=config["DB_PASSWORD"],
        dsn=config.get("DB_SERVICE") or config["RAG_DB_DSN"],
        config_dir=wallet, wallet_location=wallet,
        wallet_password=config.get("DB_WALLET_PASSWORD") or config.get("WALLET_PASSWORD"),
    )


def check_target(connection, expected):
    with connection.cursor() as cursor:
        cursor.execute("SELECT SYS_CONTEXT('USERENV','DB_NAME') FROM dual")
        name = cursor.fetchone()[0].upper()
    if name != expected.upper() and not name.endswith("_" + expected.upper()):
        raise RuntimeError("Refusing setup: database identity does not match expected target.")
    print("Verified database:", name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-env", type=Path, default=ROOT.parent / ".env")
    parser.add_argument("--app-env", type=Path, default=ROOT / ".env")
    parser.add_argument("--expected-db", default="paulparkdbaws")
    parser.add_argument("--schema", default="THEMEPARK")
    args = parser.parse_args()
    schema = args.schema.upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,29}", schema) or schema == "ADMIN":
        raise RuntimeError("Choose a dedicated application schema.")
    admin = dict(dotenv_values(args.admin_env))
    with connect(admin) as connection, connection.cursor() as cursor:
        check_target(connection, args.expected_db)
        cursor.execute("SELECT COUNT(*) FROM dba_users WHERE username=:name", name=schema)
        exists = cursor.fetchone()[0] != 0
        if args.app_env.exists():
            app = dict(dotenv_values(args.app_env))
            if app.get("DB_USERNAME") != schema:
                raise RuntimeError("Existing app env belongs to another schema; choose a separate --app-env.")
        else:
            if exists:
                raise RuntimeError("Schema already exists: supply its credentials in --app-env; no password is reset.")
            app = {
                "DB_USERNAME": schema, "DB_PASSWORD": "Tp9_" + secrets.token_hex(24),
                "DB_SERVICE": admin.get("DB_SERVICE") or admin["RAG_DB_DSN"],
                "TNS_ADMIN": admin.get("TNS_ADMIN") or admin["DB_WALLET_DIR"],
                "DB_WALLET_PASSWORD": admin.get("DB_WALLET_PASSWORD") or admin.get("WALLET_PASSWORD", ""),
                "DDS_AVA_PASSWORD": "Ava9_" + secrets.token_hex(24),
                "DDS_LEO_PASSWORD": "Leo9_" + secrets.token_hex(24),
                "MEMORY_PORT": "8091", "MEMORY_PYTHON_PORT": "8092",
            }
            with os.fdopen(os.open(args.app_env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
                stream.write("# Private generated app credentials. Never commit or publish.\n")
                for key, value in app.items():
                    stream.write(f"{key}={shlex.quote(value)}\n")
        if not exists:
            password = app["DB_PASSWORD"].replace('"', '""')
            cursor.execute(f'CREATE USER {schema} IDENTIFIED BY "{password}" DEFAULT TABLESPACE DATA QUOTA 250M ON DATA')
        cursor.execute(f"GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE VIEW, CREATE PROCEDURE, CREATE TRIGGER, CREATE TYPE, CREATE JOB, CREATE MINING MODEL, CREATE PROPERTY GRAPH TO {schema}")
        cursor.execute(f"GRANT CTXAPP TO {schema}")
        cursor.execute(f"GRANT EXECUTE ON CTXSYS.CTX_DDL TO {schema}")
        cursor.execute(f"GRANT EXECUTE ON DBMS_VECTOR TO {schema}")
    with connect(app) as connection, connection.cursor() as cursor:
        check_target(connection, args.expected_db)
        cursor.execute("SELECT COUNT(*) FROM user_mining_models WHERE model_name='ALLMINILM'")
        if cursor.fetchone()[0] == 0:
            uri = os.environ.get("OAM_MODEL_URI")
            if not uri:
                # Reuse the existing repository's public model fixture URL.
                source = ROOT / "test-utils/src/main/java/com/oracle/ojdbc/agentmemory/examples/AllMiniLmInstaller.java"
                block = source.read_text().split("DEFAULT_MODEL_URI =", 1)[1].split(";", 1)[0]
                uri = "".join(re.findall(r'"([^\"]+)"', block))
            print("Loading ALLMINILM in the application schema...")
            # Client-side download and BLOB import avoid DBMS_CLOUD privileges.
            blob = connection.createlob(oracledb.DB_TYPE_BLOB)
            try:
                with urlopen(uri, timeout=120) as response:
                    offset = 1
                    while chunk := response.read(1024 * 1024):
                        blob.write(chunk, offset)
                        offset += len(chunk)
                cursor.execute("BEGIN DBMS_VECTOR.LOAD_ONNX_MODEL(model_name=>'ALLMINILM', model_data=>:model); END;", model=blob)
            finally:
                try:
                    blob.close()
                except oracledb.DatabaseError as error:
                    # The import can consume/invalidate the temporary locator.
                    if error.args[0].code != 64219:
                        raise
        cursor.execute("SELECT VECTOR_DIMENSION_COUNT(VECTOR_EMBEDDING(ALLMINILM USING 'theme park' AS DATA)) FROM dual")
        if cursor.fetchone()[0] != 384:
            raise RuntimeError("ALLMINILM must return 384 dimensions.")
    print("Application schema and 384-dimensional ALLMINILM ready. Credentials saved privately.")


if __name__ == "__main__":
    main()
