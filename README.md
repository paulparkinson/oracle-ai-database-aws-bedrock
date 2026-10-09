# Oracle + Bedrock RAG smoke test

The [main blog](blog.html#walkthrough) embeds a three-minute narrated RAG application/source walkthrough with English captions and exact model IDs. [Download the video](rag/video/walkthrough.mp4). NL2SQL in the article is illustrative, not a running demo; no NL2SQL model has been verified.

**Live end-to-end verification passed on October 9, 2026.** Start with the
[interactive RAG demo and run instructions](rag/README.md) and
[tested walkthrough](rag/blog.html). `rag/` contains the new focused demo;
`memory/` remains the separate agent-memory application; the root smoke test
remains the compatibility entry point. [Restart checkpoint](RESUME.md).

Standalone repository: [paulparkinson/oracle-ai-database-aws-bedrock](https://github.com/paulparkinson/oracle-ai-database-aws-bedrock). See [migration notes](MIGRATION.md) and [included skills](AGENTS.md).

This small integration test calls real services with three synthetic documents:

1. Amazon Titan Text Embeddings V2 embeds each document and the question.
2. Oracle AI Database performs cosine vector retrieval with `VECTOR_DISTANCE`.
3. Amazon Nova Lite answers using only the retrieved documents.
4. The test checks that Oracle ranked the expected document first and that the
   answer contains the expected fact (`37 hours`) and `[TRANSFER_POLICY]` citation.

Oracle receives the fixture as a bound JSON document, uses `JSON_TABLE` and
`TO_VECTOR` to perform retrieval, and returns the top two chunks. This deliberately
tests RAG **without creating tables or changing existing data**. It is not a
persistent ingestion/index benchmark and does not read your business documents.
No Bedrock Knowledge Base is needed. See [the blog](blog.html) for the larger design.

## Verification status (October 9, 2026)

The full RAG smoke test passed with real Titan V2 embeddings, live Oracle
retrieval and Nova Lite generation. Oracle ranked `TRANSFER_POLICY` first
(cosine distance 0.076545), and the answer returned `37 hours [TRANSFER_POLICY]`.
The interactive browser also passed warranty, recycling and insufficient-evidence
cases. No persistent database data was changed. Four offline regression checks
and JavaScript syntax checks passed; these are separate from the live checks.

The current RAG demo uses AWS SSO plus a separately configured Oracle login.
It is not an EKS passwordless-authentication result. Quick signup was attempted
after approval and returned AccessDeniedException; no subscription was created.

No admin change is currently needed for these two models: use the assigned Bedrock
role. The [example policy](bedrock-invoke-policy.json) documents the narrow direct
invocation permissions for the default models; it was not applied. An approved
inference profile needs corresponding profile and destination-model permissions;
provider onboarding and organization policies may impose additional requirements.

## Setup

Use Python 3.10+ and run from this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

Fill in `.env` locally. Use **paulparkdbaws**, the database created in AWS account
`054037143469`, region `us-east-1`. Use a TCPS EZConnect+ DSN with the exact
host/service from the database connection information, not the placeholder.
The existing database requires mTLS. Python Thin mode needs the extracted wallet
directory including `ewallet.pem`, plus the wallet password if
the PEM key is encrypted. The wallet password is distinct from the database-user
password. A user able to connect and run the SELECT expressions is sufficient;
no `CREATE TABLE` privilege or administrator account is required.

The test uses `RAG_DB_*` variables to avoid accidentally using another project's
`ORACLE_*` settings. It also accepts this project's existing `DB_USERNAME`,
`DB_PASSWORD`, `DB_WALLET_DIR` (or `TNS_ADMIN`), and `DB_WALLET_PASSWORD`
(or `WALLET_PASSWORD`) settings;
`RAG_DB_*` takes precedence. Set `RAG_DB_DSN=tcps://host:1522/service` using
the actual low-service host/name for the target database.
It verifies the AWS account and Oracle database/service name
before the RAG model calls. Override the `RAG_EXPECTED_*` settings only when
intentionally testing a different target. No passwords, wallets, or tokens belong
in Git or chat.

## AWS authentication

An AWS browser session does not authenticate local Python. Use an existing AWS SDK
profile, temporary environment credentials, or an AWS workload role. For AWS CLI v2
SSO setup:

```sh
aws configure sso --profile oracle-bedrock
aws sso login --profile oracle-bedrock
export AWS_PROFILE=oracle-bedrock
```

Use access portal `https://d-9067d4cd70.awsapps.com/start/`, account `054037143469`,
and permission set **Multicloud-Engineering-Bedrock** (not Field-Engineering-Standard).
Select workload region `us-east-1`. The SSO directory region is a separate setting;
use the organization's configured value when setting up the CLI.
The role must allow `bedrock:InvokeModel` for the embedding and generation models.
Converse uses that same inference permission. This script does not need model-list,
Knowledge Base creation, or streaming permissions. AWS STS is used to identify the
account. If Nova Lite direct inference is unavailable, set `RAG_TEXT_MODEL` to an
approved Converse-compatible model or inference-profile ID. Cross-region profiles
may route processing to other regions and require permissions for those models.
`RAG_EMBED_MODEL` must be Titan V2-compatible and return 1,024 float dimensions.

## Run

```sh
# Optional: isolate Bedrock permissions and connectivity (not an Oracle/RAG test).
python rag_smoke_test.py --bedrock-only

# Full smoke test: 4 embedding invocations and 1 generation invocation.
python rag_smoke_test.py
```

Model invocations incur normal Bedrock charges. The fixture is small and uses
synthetic data only. Success ends with:

```text
PASS: Bedrock embeddings -> Oracle vector retrieval -> grounded Bedrock answer.
No database objects or rows were created or changed.
```

That output was observed in the verified run; new environments must rerun it. A failure exits
nonzero. `--bedrock-only` explicitly reports that Oracle was not tested. The test
prints document IDs, distances, and the answer; it does not print credentials or
document embeddings. The fixed fact/citation check is a smoke assertion, not a
comprehensive evaluation of groundedness or authorization.

For a separate environment file:

```sh
python rag_smoke_test.py --env-file /secure/path/bedrock-rag.env
```

## Troubleshooting

- **NoCredentialsError / expired SSO:** authenticate the local SDK profile again.
- **AccessDeniedException:** check model invocation permissions, organization
  restrictions, and model/provider onboarding; console access alone is insufficient.
- **ValidationException:** check the chosen model ID, region, and inference-profile
  requirements. The generation model must support Converse and its parameters.
- **Oracle TLS / connection error:** verify this database's wallet, service alias,
  credentials, firewall/VPN route, and the wallet's PEM password.
- **Database-name mismatch:** confirm that the DSN selects `paulparkdbaws`. Do not
  weaken the expected-name check simply to reuse another project's connection.
- **Retrieval assertion:** ensure all embeddings use the same model/dimensions and
  inspect the reported ranking; no approximate index is used in this tiny test.

References: [Titan embedding parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-embed-text.html),
[Converse](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html),
[Oracle vector binding](https://python-oracledb.readthedocs.io/en/stable/user_guide/vector_data_type.html).

## Migrated Oracle AI Agent Memory demo

The complete memory application is under [`memory/`](memory/). Use
[`docs.md`](docs.md) to deploy the full Java app shown in the theme park video
and the Python companion to an existing AWS instance with `paulparkdbaws`.
The instance deployment scripts are in [`memory/aws/`](memory/aws/).
Use
[`memory/README.md`](memory/README.md) for the local Python and Java lanes,
database inspector, Deep Data Security proof, Memory Quest, and walkthrough
source. For AWS container deployment and the separate Bedrock verification
path, see [`memory/aws/README.md`](memory/aws/README.md) and the reusable
[`oracle-memory-aws-bedrock` skill](skills/oracle-memory-aws-bedrock/SKILL.md).

The memory browser and Bedrock RAG smoke test are intentionally separate
verification lanes: the browser demonstrates Oracle Agent Memory and
database-resident retrieval, while `rag_smoke_test.py` verifies Titan
embeddings, Oracle vector retrieval, and Nova Lite grounded generation.
