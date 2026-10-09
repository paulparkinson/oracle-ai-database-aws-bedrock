# Live Oracle + Bedrock RAG and read-only NL2SQL demo

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

The web app binds only loopback. RAG accepts four bounded policy questions; NL2SQL accepts up to 500 characters but only one restricted query grammar. It validates Host and Origin; it exposes no arbitrary SQL, credentials or database identifiers. It is a workstation demo backed by cloud services, **not an AWS-hosted public application**. Do not change the bind address to publish it. Production needs a real application server, authentication, authorization, limits and a least-privilege database identity.

## Architecture and verification

`Browser → Python → Titan V2 → Oracle VECTOR_DISTANCE → Nova Lite → cited answer`

- `app.py` checks the AWS account and Oracle database/service before model requests, then starts a read-only transaction.
- `rag_smoke_test.py` supplies three synthetic fixture documents and the actual SQL. Documents and 1,024-dimensional embeddings are bound through a temporary CLOB locator; the question is a native VECTOR bind. Oracle ranks two chunks with exact cosine search.
- Nova receives only the question and those chunks, with an instruction to abstain when unsupported. This small test is not a general hallucination or authorization evaluation.
- The explicit CLOB locator fixes the observed `ORA-01460` with the large real-embedding payload; a short synthetic-vector test had not exposed it. Connection teardown releases temporary resources.
- This implementation has no permanent ingestion table, vector index, Bedrock Knowledge Base, MCP endpoint or agent write action.

## Read-only NL2SQL

In the same app, choose **Read-only NL2SQL**:

1. Enter `List the top 3 inventory items with stockout risk at least 70.`
2. Click **Generate SQL**. Inspect Nova Lite's SQL and the Bedrock request ID. No Oracle query has run yet.
3. Click **Run reviewed SELECT**. Oracle returns DEMO-100 (92), DEMO-200 (81), and DEMO-300 (74).
4. Try `Show items with risk at least 85, limit 5.` → one row.
5. Try `Show items with risk at least 95, limit 3.` → no rows.
6. Try `Delete all inventory records.` → unsupported; no SQL executes.

These are **five synthetic fixture rows**, not business inventory. Risk is a demo score from 0 to 100, not a probability. Oracle evaluates the fixture through bound JSON and `JSON_TABLE`; no persistent table is created.

`Browser → Bedrock Nova Lite → validate SQL → review → fixed bound Oracle SELECT → rows`

- NL2SQL uses **Amazon Nova Lite**, `amazon.nova-lite-v1:0`, through Bedrock Converse. It does **not** use embeddings.
- This is **application-managed NL2SQL**, not Oracle Select AI: Python calls Bedrock; Oracle executes the read-only relational query.
- [nl2sql.py](nl2sql.py) accepts exactly one complete SELECT grammar: fixed columns and fixture relation, a numeric minimum risk, descending risk/sku ordering, and a bounded row limit.
- Raw model SQL is **never executed**. The validator extracts the two integers; the equivalent fixed Oracle query binds those values and the fixture. Expand “Fixed Oracle query and bound parameters” to inspect this distinction.
- Server-side review receipts expire after ten minutes and are single-use. The execution route accepts a receipt, not client-supplied SQL. Changing the question invalidates the UI review.
- Unknown schemas, functions, comments, joins, extra statements, writes and unsupported query shapes fail closed. There is no fallback answer or cached generated SQL.
- The model sees the question and synthetic schema, not database rows. Results come from Oracle without another LLM summarization.
- The fixed grammar is intentionally narrow, not a general SQL sandbox. Production must use a least-privilege account; the existing demo login is ADMIN, and this work does not change its grants.

Verified 2026-10-09: live Nova Lite generation followed by Oracle execution returned 3/1/0 rows for thresholds 70/85/95. A delete request was rejected without execution. Browser review and result captures are included in the video. Twelve offline tests cover SQL boundaries, review receipts and RAG response/citation validation. RAG also passed fresh transfer, warranty and insufficient-evidence browser checks.

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
