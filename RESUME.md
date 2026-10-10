# AWS demo checkpoint

## AgentCore extension

- Added agentcore_demo Runtime adapter, IAM-signed client and allowlisted ARM64 ZIP builder.
- Local SDK HTTP test passed with live RAG (37 hours), live NL2SQL (3 rows), cross-session rejection and replay rejection; 6 adapter plus 12 existing tests pass.
- ZIP builds; no private .env/wallet/credentials included (SDK public CA bundle is expected).
- Cloud deployment NOT performed: ListAgentRuntimes denied; Create/Invoke Runtime, CreateRole/PassRole and Secrets Manager actions simulate implicitDeny.
- Next: administrator supplies scoped permissions/execution role and a dedicated CREATE SESSION-only Oracle user's secret; approve and verify Runtime network access. Existing Oracle DNS is public from this workstation, not proof of Runtime reachability.
- Do not upload the existing ADMIN credential/wallet or enable local-mode bypass in cloud. No VM, role, bucket, secret or Runtime created.

Updated 2026-10-09. Combined RAG/NL2SQL video built and verified; inspect git/Pages status to confirm publication.

- AWS SSO renewed successfully. Private SDK cache only; no credentials in commits.
- Live RAG: Titan V2 embeddings → Oracle cosine retrieval → Nova Lite cited answer. Fresh browser tests pass for transfer (37 hours), warranty (18 months), and missing Aspen evidence. Structured response validation rejects malformed answers and unknown citation IDs.
- Live NL2SQL: Nova Lite generation → complete SELECT grammar validation → review receipt → fixed bound Oracle query. Thresholds 70/85/95 return 3/1/0 rows. Delete request rejected. No persistent database changes.
- Twelve offline safety tests pass. Browser confirms the question input becomes editable after execution.
- Combined video: fifteen 18-second scenes (270 seconds), narration plus SRT/VTT, edited real browser captures and current source. Full decode passed: 6,480 video frames and 742 audio samples. All scene previews inspected; media/embed audit passed. Browser playback and English captions verified, responsive video fits a 390-pixel viewport.
- Application-managed NL2SQL is not database-side Select AI. The article's Select AI and broader supply-chain examples remain illustrative.
- Local app: `python rag/app.py`, loopback 8095; AWS profile `oracle-demo`; private repository-root `.env`. Never serve the repository root publicly.
- Rebuild in `rag/video`: `swift -sdk /Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk build.swift`; verify with `verify.swift` using the same SDK.
- Quick Enterprise creation returned AccessDeniedException; no subscription/user was created. Existing role simulations deny EKS cluster/IAM role creation. These experiments remain blocked on effective permissions; the RAG/NL2SQL demo does not depend on them.
- Resume by reading AGENTS.md, README.md, this file, git status and the video-blog-walkthrough skill. Do not replay provisioning or expose secrets.
