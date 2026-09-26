# AWS memory + Bedrock walkthrough plan

This is the AWS companion to the 16-step memory walkthrough. It is intentionally
honest about the two runnable lanes: the ECS container hosts the Oracle Agent
Memory browser, while the Bedrock smoke test independently proves model calls,
Oracle vector retrieval, and grounded generation.

| Scene | Visual | Narration focus | Evidence |
| --- | --- | --- | --- |
| 1 | Architecture title card | ECS/Fargate hosts the browser; Oracle stores memory; Bedrock is a separately verified RAG lane. | `memory/aws/README.md` |
| 2 | `memory/aws/Dockerfile` and task configuration | The image contains code and dependencies, never wallets or passwords. | Read-only wallet mount and Secrets Manager variables |
| 3 | Oracle connection configuration | Private network routing and mTLS are prerequisites for the database endpoint. | `TNS_ADMIN`, service alias, least-privilege user |
| 4 | Browser memory lane | Retain, recall, refine, TTL, Deep Data Security, quest, GraphRAG, and consented AR run against Oracle. | Existing `memory/video` 16-step source/captions |
| 5 | `rag_smoke_test.py --bedrock-only` | Titan and Nova Lite calls use the task/developer role; no database writes occur in this mode. | Account identity and model response |
| 6 | `rag_smoke_test.py` | Retrieved synthetic documents are ranked by Oracle `VECTOR_DISTANCE` and supplied as grounded evidence. | Expected citation and `37 hours` assertion |
| 7 | Security recap | Keep Bedrock permissions narrow, validate the database target, and never publish secrets. | `memory/aws/bedrock-invoke-policy.json` and audit checks |

The existing `build-video.swift` remains the reproducible source for the live
memory application walkthrough. Capture AWS scenes only after a real ECS and
Bedrock run is available; do not fabricate cloud evidence from local screenshots.
