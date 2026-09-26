# Run the memory demo on AWS

This deployment runs the Python Oracle AI Agent Memory browser application in
an ECS/Fargate task and connects it to Oracle Database@AWS over a private
network path. It does not put a wallet, password, or AWS key in the container
image.

## What is and is not Bedrock-enabled

The public memory lane deliberately uses `oracleagentmemory` keyword search and
the database-resident `ALLMINILM` model for the Memory Quest vector lane. It
does not need an external LLM key and the browser application does not claim to
call Bedrock. The repository's root `rag_smoke_test.py` is the Bedrock path:
Titan embeddings, Oracle vector retrieval, and Nova Lite grounded generation.
Run that smoke test separately from a task role with the policy in
`bedrock-invoke-policy.json`.

This separation is intentional: it prevents an AWS deployment guide from
claiming that a memory lifecycle demo has exercised Bedrock when it has not.
To add Bedrock extraction or generation to the memory UI, implement and test a
provider behind the application's memory-extraction boundary, keep retrieval
and authorization in Oracle, and update the video and verification status
together.

## Prerequisites

1. An Oracle Database@AWS or Autonomous AI Database endpoint reachable from
   the ECS VPC, with a least-privilege application schema and an mTLS wallet.
2. A private route from the ECS subnets to the database endpoint (and security
   groups/NACLs that permit the database listener). Public internet is not a
   substitute for database reachability.
3. An ECR repository, ECS cluster, task execution role, task role, and a load
   balancer or other controlled ingress.
4. A wallet stored in a controlled secret or mounted encrypted volume. Mount
   it read-only at `/run/secrets/oracle-wallet`; do not bake it into the image.

## Build and run

From the repository root:

```bash
docker build -f memory/aws/Dockerfile -t oracle-memory:local memory
```

Push the image to ECR, then configure the ECS task with these environment
variables (use Secrets Manager for passwords):

```text
DB_USERNAME=<application user>
DB_PASSWORD=<secret>
DB_SERVICE=<wallet service alias>
TNS_ADMIN=/run/secrets/oracle-wallet
MEMORY_PYTHON_PORT=8092
```

The wallet mount must contain `tnsnames.ora` and the files required by the
selected Python Thin-mode connection. Health-check the service at
`/api/health`, then run `memory/python-agent/smoke-test.sh` through the
controlled service URL. Run the browser demonstration in the order documented
by `memory/README.md`.

## Bedrock verification

Authenticate the ECS task role or a temporary developer role in the same AWS
account and region, then run:

```bash
python3 rag_smoke_test.py --bedrock-only
python3 rag_smoke_test.py
```

The full test verifies account identity, Bedrock embeddings, read-only Oracle
vector retrieval, and a grounded Nova Lite answer using synthetic documents.
It does not create tables or modify business data. Set `RAG_DB_*` variables as
described in the root README. Bedrock model availability, provider onboarding,
cross-region inference rules, and organization policies remain account-specific.

## Operational checks

- Confirm the database identity and service alias before sending model input.
- Keep wallet files and passwords in Secrets Manager/EFS controls, never Git or
  image layers.
- Restrict the ECS task role to the selected Bedrock model ARNs if the task
  invokes Bedrock; do not grant model listing or Knowledge Base administration
  unless required.
- Use synthetic data for smoke tests and review logs for prompt, wallet, and
  token leakage before enabling production traffic.
- Treat `memory/java-agent` as a separate demonstration lane. It requires
  Java 21, the local `ojdbc-agent-memory` build, and Ollama; do not deploy it
  with the Python container without packaging those dependencies explicitly.
