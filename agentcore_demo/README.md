# AgentCore Runtime: Oracle + Bedrock demo

## Status and scope

**Local verification passed (2026-10-09):** actual SDK /invocations and /ping,
live Bedrock RAG and NL2SQL generation, real Oracle retrieval/SELECT, cross-session
receipt denial and replay denial. Six adapter tests plus twelve existing tests pass.
The Linux ARM64 ZIP builds and excludes private configuration/wallets; the SDK's
public CA certificate bundle is included. Cloud Runtime execution and Secrets
Manager retrieval have not been validated.

This addition hosts the existing bounded RAG and reviewed NL2SQL operations behind
Amazon Bedrock AgentCore Runtime's invocation API. It is not an autonomous
agent loop, AgentCore Gateway, Memory, or a new public web frontend. The existing
browser demo is unchanged. The published video still demonstrates the original
local application, not AgentCore.

**Cloud deployment is blocked, not completed.** On 2026-10-09 the current
Multicloud-Engineering-Bedrock role in account 054037143469 / us-east-1 received
AccessDenied for ListAgentRuntimes. IAM simulation returned implicitDeny for
CreateAgentRuntime, InvokeAgentRuntime, CreateRole, PassRole, CreateSecret and
GetSecretValue. S3 CreateBucket/PutObject simulated allowed; this is not proof
of complete deployment permission.

**No EC2 VM or EKS cluster is needed.** Use managed Runtime with a Linux ARM64
Python ZIP. One Runtime, an existing/private S3 artifact bucket, a dedicated
execution role, a Secrets Manager secret, and logs are sufficient for this
integration, subject to Oracle network access. Runtime, inference, secrets,
storage and optional networking incur charges.

`IAM-signed caller → AgentCore Runtime → existing RAG / NL2SQL code → Bedrock + Oracle`

RAG uses Titan Text Embeddings V2 and Nova Lite. NL2SQL uses Nova Lite, requires
separate generate/review/execute requests, and executes only fixed bound SQL.
Synthetic fixtures are unchanged. There is no Toolkit, Google Search or fake
fallback. Runtime execution-role credentials replace workstation AWS SSO for
Bedrock calls, **not** Oracle database authentication.

## What the AWS administrator must provide

| Identity | Required scoped access |
|---|---|
| Deployer | AgentCore List/Get/Create/Update Runtime, endpoint management if used, InvokeAgentRuntime for testing; PassRole on the one approved execution role; artifact S3 Put/GetObject |
| Runtime execution role | Trust bedrock-agentcore.amazonaws.com with source-account/source-ARN restrictions; InvokeModel on Titan V2 and Nova Lite; GetSecretValue on the one Oracle secret; artifact S3 GetObject and required CloudWatch logging permissions |
| Caller | InvokeAgentRuntime on this Runtime/endpoint only |
| Secret owner | Create/update the one secret; KMS permissions if using a customer-managed key |
| VPC administrator, if required | Approved subnets/security group, Oracle TCPS routing/DNS, AWS service endpoints or NAT, and AgentCore network service-linked role |

The deployer does not need CreateRole if an administrator creates the role.
Do not grant blanket administrator access or assume an IAM simulation accounts
for every SCP/resource policy. No roles, secrets, runtimes or buckets were created
by this change.

Use a dedicated Oracle user with **CREATE SESSION only** for these fixture reads;
the cloud adapter rejects ADMIN/SYS/SYSTEM. Provisioning that user is a separate
database change. Store secret JSON privately with keys `user`, `password`,
`dsn` (TCPS EZConnect+), and, for mTLS, `wallet_pem` and `wallet_password`.
Do not put secret values in Runtime environment variables, source, the ZIP or
shell arguments. Only the secret ARN belongs in Runtime configuration.
The PEM is written at runtime into a private temporary directory with mode 0600.

The workstation's successful Oracle connection does not prove Runtime reachability.
The current Oracle hostname resolves to public IPs from this workstation.
Use VPC mode if Oracle is private or requires controlled egress. Public network
mode is only suitable if the Oracle endpoint and existing policies permit it;
do not open the database to all IPs. No firewall or network change is made here.

## Local SDK test (no AgentCore cloud permission needed)

From the repository root, use a separate environment because the AgentCore SDK
requires a newer boto3 than the original demo's pin:

```sh
python3 -m venv .runtime/agentcore-venv
.runtime/agentcore-venv/bin/python -m pip install -r agentcore_demo/requirements.txt
.runtime/agentcore-venv/bin/python -m unittest agentcore_demo.test_runtime -v
.runtime/agentcore-venv/bin/python -m unittest discover -s rag/tests -v
AWS_PROFILE=oracle-bedrock AGENTCORE_DEMO_LOCAL=1 \
  .runtime/agentcore-venv/bin/python -m agentcore_demo.runtime
```

The explicit local mode loads the existing private root .env and binds loopback
8080. It is not a public authentication boundary. Never expose this dev server.

```sh
curl http://127.0.0.1:8080/invocations \
  -H 'Content-Type: application/json' \
  -H 'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: 11111111-1111-4111-8111-111111111111' \
  -d '{"operation":"nl2sql.generate","question":"List the top 3 inventory items with stockout risk at least 70."}'
```

Inspect the returned SQL; then send `{"operation":"nl2sql.execute","receipt":"RETURNED_RECEIPT"}`
using the same session header. For RAG, send
`{"operation":"rag","question":"For Project Cedar, how many hours before shipment must a warehouse transfer be approved?"}`.
Health endpoint: `GET /ping`.

Receipts are single-use, session-bound and expire after ten minutes. Runtime
termination loses them; generate/review again. This is a single-operator demo.
A shared backend must bind sessions to authenticated users; session IDs are not
authentication. No multi-user frontend or durable review store is claimed.

## Cloud deployment after permissions and connectivity are approved

1. Build the allowlisted archive:
   ` .runtime/agentcore-venv/bin/python -m agentcore_demo.package `.
   Output: ignored `.runtime/agentcore.zip`; only pinned dependencies and listed
   source files are included, never .env, wallets, videos or the repository tree.
2. Upload it to an approved private S3 bucket in us-east-1. The execution role
   must be able to read the exact object.
3. Use the AgentCore console or CreateAgentRuntime API with Python 3.13,
   codeConfiguration pointing to that object, entryPoint
   `["agentcore_demo/main.py"]`, and the approved role ARN.
4. Set nonsecret environment variables `ORACLE_SECRET_ARN`,
   `RAG_EXPECTED_AWS_ACCOUNT=054037143469`, `RAG_EXPECTED_DB_NAME=paulparkdbaws`,
   `RAG_AWS_REGION=us-east-1`, and `AWS_DEFAULT_REGION=us-east-1`.
   **Do not set AGENTCORE_DEMO_LOCAL in the cloud.**
5. Select the approved network configuration and IAM invocation authentication.
   Set an idle session timeout of 300 seconds and maximum lifetime of 1800 seconds.
   Wait until the Runtime is READY.
6. Invoke with the signed client (no browser AWS credentials):
```sh
.runtime/agentcore-venv/bin/python -m agentcore_demo.invoke \
  --runtime-arn YOUR_RUNTIME_ARN \
  '{"operation":"nl2sql.generate","question":"List the top 3 inventory items with stockout risk at least 70."}'
```
   Copy its session ID into `--session` for the reviewed execute operation.
7. Require real cloud results: risk thresholds 70/85/95 give 3/1/0 rows;
   transfer RAG returns 37 hours with the Oracle-retrieved policy; unsupported
   writes, cross-session receipts and replays fail. Do not claim deployment
   success based only on local SDK tests.
8. Stop test sessions with StopRuntimeSession. If retiring the deployment, delete
   only this demo Runtime and its dedicated artifact/secret/role after checking
   ownership; never remove shared database or networking resources.

## References

- [Runtime direct Python deployment](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-code-deploy-python.html)
- [Runtime permissions and trust](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)
- [Runtime VPC connectivity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html)

