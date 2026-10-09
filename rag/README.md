# Live Oracle + Bedrock RAG demo

**Verified 2026-10-09:** real Titan V2 embeddings, Oracle cosine retrieval and Nova Lite generation pass end to end. The browser demo uses three explicitly synthetic policies, not business documents. No persistent database objects or rows are changed.

[Walkthrough article](blog.html) · [Application](app.py) · [Core SQL/model code](../rag_smoke_test.py)

## Run

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env  # only when .env does not already exist
chmod 600 .env
aws configure sso --profile oracle-bedrock
aws sso login --profile oracle-bedrock
export AWS_PROFILE=oracle-bedrock
.venv/bin/python rag_smoke_test.py
.venv/bin/python rag/app.py
```

Fill the private `.env` before running: AWS account/region guards; TCPS **EZConnect+** DSN (`tcps://host:1522/service`); Oracle login and mTLS wallet directory/password when needed. Obtain the exact host/service from the database connection information. Keep server-certificate checking enabled. The example hostname is not a deployment endpoint. A dedicated user with `CREATE SESSION` is sufficient for this fixture; ADMIN is not required. Our initial integration run used the existing configured ADMIN login, not workload identity.

Open **http://127.0.0.1:8095**, choose a question, and click **Run live RAG**:

1. Project Cedar transfer approval → **37 hours**, `TRANSFER_POLICY` ranked first.
2. Project Cedar sensor warranty → **18 months**, `WARRANTY_POLICY` ranked first.
3. Project Maple recycling → **Fridays**, `RECYCLING_POLICY` ranked first.
4. Project Aspen transfer policy → evidence is insufficient; no Aspen policy is in the fixture.

Every click invokes live services (four embeddings plus one generation). Answers are not cached. Normal Bedrock charges apply. Wording can vary. The browser displays exact retrieved text and cosine distances before the model’s answer is interpreted. A citation alone is not proof of groundedness: compare it with the displayed evidence.

The web app binds only loopback and accepts only four bounded questions. It validates Host and Origin; it exposes no arbitrary SQL, credentials or database identifiers. It is a workstation demo backed by cloud services, **not an AWS-hosted public application**. Do not change the bind address to publish it. Production needs a real application server, authentication, authorization, limits and a least-privilege database identity.

## Architecture and verification

`Browser → Python → Titan V2 → Oracle VECTOR_DISTANCE → Nova Lite → cited answer`

- `app.py` checks the AWS account and Oracle database/service before model requests, then starts a read-only transaction.
- `rag_smoke_test.py` supplies three synthetic fixture documents and the actual SQL. Documents and 1,024-dimensional embeddings are bound through a temporary CLOB locator; the question is a native VECTOR bind. Oracle ranks two chunks with exact cosine search.
- Nova receives only the question and those chunks, with an instruction to abstain when unsupported. This small test is not a general hallucination or authorization evaluation.
- The explicit CLOB locator fixes the observed `ORA-01460` with the large real-embedding payload; a short synthetic-vector test had not exposed it. Connection teardown releases temporary resources.
- This implementation has no permanent ingestion table, vector index, Bedrock Knowledge Base, MCP endpoint or agent write action.

## Amazon Quick result

The existing account had no subscription in `us-east-1`. The user approved one Enterprise demo user. `CreateAccountSubscription` with existing IAM federation returned **AccessDeniedException**. No subscription or user was created and no Quick demo was claimed. IAM policy simulation reported the signup action allowed, so an administrator must inspect effective restrictions/service prerequisites; the exact denial source is not established.

A future Quick integration can expose bounded `ask_policy` retrieval through a secured remote MCP server. It needs an Enterprise subscription and a permitted network/authentication path. Do not expose this loopback server or Oracle credentials as a shortcut. [AWS MCP integration](https://docs.aws.amazon.com/quick/latest/userguide/mcp-integration.html) · [Quick signup](https://docs.aws.amazon.com/quick/latest/userguide/signing-up.html).

## Recovery and tests

After a reboot, reopen the repository, read [RESUME.md](../RESUME.md), renew SSO if expired, and run the smoke test before starting the app. No cloud infrastructure from this investigation needs cleanup. Stop the local app with Ctrl-C.

```sh
.venv/bin/python -m unittest discover -s rag/tests -v
node --check rag/app.js
```

For the separate passwordless EKS experiment, see [workload-identity-eks](https://github.com/paulparkinson/oracledb-java-security/tree/main/workload-identity-eks). Neither AWS SSO nor a successful password-authenticated Oracle session proves pod identity authentication.
