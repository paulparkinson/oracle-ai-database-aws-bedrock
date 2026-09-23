# Repository guidance

Use `rag_smoke_test.py` and README.md for the Oracle/Bedrock integration. Local configuration is in `.env`; the template is `.env.example`.

Keep credentials, wallets, caches, and generated build files out of commits.
Run checks appropriate to the changed component. Repository relocation does not
change existing cloud resources or running deployments.

## Included skills

The complete shared skill package is in
`skills/video-blog-walkthrough/SKILL.md`, with its agent metadata and audit script.
It is discoverable through `.agents/skills/video-blog-walkthrough`.
Read this skill when creating narrated developer-blog walkthroughs.
Application tool and agent skill definitions remain with their implementations.
