# AWS demo checkpoint

Updated 2026-10-09 UTC. Work in progress; not a completion report.

## Current video request

- Root blog now embeds the expanded three-minute RAG walkthrough with exact model IDs, narration, SRT/VTT captions, application captures and source. Result captures are from the earlier successful live runs, not a newly authenticated run.
- NL2SQL is not implemented in this repository: the root article contains a placeholder Select AI profile/model. Read-only inspection returned no profiles or profile attributes for the configured Oracle login. Do not claim a tested NL2SQL model.
- Pending user choice: add a bounded application-managed Nova Lite NL2SQL demo, or keep this video RAG-only with Select AI clearly illustrative.
- Previous temporary AWS CLI/profile files are gone. A new live RAG request failed before inference. AWS device sign-in redirects to Oracle corporate sign-in; browser safety review requires explicit approval for that destination. Do not bypass it.
- Temporary preview servers and auth sessions are not durable; restart as needed. Only explicitly public blog/media routes may be exposed, never the repository root or private environment.
- Expanded video verification passed: 180 seconds at 1920×1080, all 4,320 video frames and 506 audio samples decoded; ten scene previews inspected; media/embed audit and four offline tests passed. Browser playback advanced with English captions visible; the responsive embed fits a phone viewport.

- Goal: test Amazon Quick with the Oracle/Bedrock RAG demo; if unavailable, validate and publish the RAG demo, blog and narrated video. Commit/push tested changes.
- User approved scoped cloud work. Never publish credentials, wallets, tokens or raw account logs.
- AWS CLI SSO login succeeded with the existing Multicloud-Engineering-Bedrock role. AWS credentials remain in the CLI-managed private cache, outside Git.
- Read-only discovery in us-east-1: EKS cluster list empty; Quick DescribeAccountSubscription returned ResourceNotFoundException (account does not exist).
- Quick Enterprise signup was explicitly approved for one demo user. CreateAccountSubscription using IAM_ONLY returned AccessDeniedException. No subscription/user was created. Both assigned roles' simulations deny EKS cluster and IAM role creation. No cloud cleanup pending.
- Full live RAG now PASSES after replacing the large JSON string bind with an explicit temporary CLOB locator. Transfer (37 hours), warranty (18 months), recycling (Fridays) and insufficient-evidence browser cases all ran against live services.
- Browser demo is in rag/app.py, loopback port 8095; stop/restart as needed. Current shell session ID is transient and must not be relied on after reboot. Read rag/README.md for the normal launch command.
- Oracle read-only diagnostics: identity_provider_type=NONE, config unset, session authentication PASSWORD. EKS passwordless login is NOT proven.
- RAG article and 126-second narrated video complete. Full audio/video decoding passed (1920×1080), all seven scene previews inspected, skill media audit passed, desktop/mobile article layouts checked. Four offline tests passed. Full smoke test also passed using TCPS EZConnect+. Check git log/status and origin before resuming to confirm the latest packaging commit/push.
- Remaining task: obtain effective EKS provisioning and Quick signup access, then resume the cloud experiments. The user approved one Quick Enterprise demo user; do not create extra subscriptions/users or assume a denied API call succeeded.
- Rebuild video with matching Swift SDK (the default macOS 27 SDK is newer than this machine's compiler): swift -sdk /Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk build.swift from rag/video. Verification uses verify.swift with the same SDK.
- Local tooling: official notarized AWS CLI 2.37.11 extracted at /private/tmp/aws-overnight.EBsCXg/awscli/aws-cli.pkg/Payload/aws-cli/aws. Non-secret SSO profile file: /private/tmp/aws-overnight.EBsCXg/config, profile oracle-demo. If reboot removes these, reinstall official AWS CLI and configure SSO using the repository README. Tokens may require renewed SSO after expiry.
- Command prefix: AWS_CONFIG_FILE=/private/tmp/aws-overnight.EBsCXg/config AWS_PROFILE=oracle-demo. Python: .venv/bin/python. Private database configuration: repository-root .env.
- Resume by reading AGENTS.md, README.md, this file, git status and skills/video-blog-walkthrough/SKILL.md. Do not replay provisioning without checking resource existence.
- Other task: ../oracledb-java-security/workload-identity-eks/README.md.
