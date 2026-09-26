---
name: oracle-memory-aws-bedrock
description: Run or deploy the migrated Oracle AI Agent Memory demo with Oracle AI Database and Amazon Bedrock verification on AWS.
metadata:
  short-description: Run the Oracle memory demo on AWS
---

# Oracle memory on AWS

Use this skill for the `memory/` application in this repository and its AWS
deployment path. Read `memory/README.md` and `memory/aws/README.md` first.

## Runtime lanes

- The Python browser lane runs on port 8092 and uses the public
  `oracleagentmemory` package, Oracle AI Database, exact identity scope, and
  the database-resident embedding lane.
- The Java lane runs on port 8091 and requires Java 21, Ollama, the local
  `ojdbc-agent-memory` build, and its shared database setup.
- The root `rag_smoke_test.py` is the Bedrock lane. It independently verifies
  Titan embeddings, Oracle vector retrieval, and Nova Lite grounded generation
  with synthetic documents.

Do not describe the memory browser as Bedrock-backed unless a tested provider
has been added to the application. Keep the memory lifecycle demo and the
Bedrock RAG smoke test as separate verification claims.

## Local run

1. Copy `memory/.env.example` to `memory/.env`; never print or commit it.
2. Start `memory/python-agent/run.sh` and run its `smoke-test.sh` separately.
3. If the Memory Quest schema is absent, initialize it with the Java lane once.
4. Use the ordered demonstration in `memory/README.md`, including the Deep
   Data Security and consent checks.

## AWS run

Use the image and network guidance in `memory/aws/README.md`. Mount the Oracle
wallet read-only, inject credentials through AWS Secrets Manager, and use an
ECS task role for AWS calls. Validate the Oracle target before any model call.
The Bedrock policy in `memory/aws/bedrock-invoke-policy.json` is a narrow
example and must be reviewed against the account's approved models and region.

## Handoff and verification

When changing the app, update the relevant README, smoke test, and walkthrough
scene plan together. Run Python syntax/tests, the app smoke test when database
access exists, and `scripts/audit_video.sh` when video assets or embedding
change. Never include wallets, `.env` files, virtual environments, build
directories, compiled jars, or generated large video files in a commit.
