# AWS demo checkpoint

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
