# AWS access needed for the demos

Status: October 10, 2026. Target region: `us-east-1`. These findings distinguish actual API denials from IAM simulation; simulation is not proof that a request will succeed. No AgentCore runtime, Quick subscription or EKS cluster was created by these tests.

## Observed blockers

| Area | Evidence | Request to administrator |
| --- | --- | --- |
| AgentCore | `bedrock-agentcore:ListAgentRuntimes` returned AccessDenied. `CreateAgentRuntime` and `InvokeAgentRuntime` simulated implicitDeny. | Scoped runtime create/get/list/update/delete/invoke access, and endpoint/session operations needed for testing. |
| IAM role | `iam:CreateRole` and `iam:PassRole` simulated implicitDeny. | Prefer an administrator-created runtime execution role; allow passing only that role to AgentCore. Alternatively delegate creation and policy management for a demo-only role prefix. |
| Oracle secret | `secretsmanager:CreateSecret` and `GetSecretValue` simulated implicitDeny. | Administrator provisions one Oracle connection secret; execution role can read it. Grant operator create/update only if operator-managed rotation is required. |
| Amazon Quick | `CreateAccountSubscription` returned AccessDeniedException although its IAM simulation was allowed. | Administrator completes Enterprise subscription for one approved demo user or resolves effective-policy/service prerequisites. Do not assume another identity-policy Allow alone fixes this. |
| EKS workload-identity experiment | Both assigned roles simulated implicitDeny for `eks:CreateCluster` and `iam:CreateRole`; no cluster was found in the tested region. | Prefer access to an existing approved cluster and namespace. Otherwise have the platform team provision an isolated cluster and associated roles. No workload database login has been tested on EKS. |

S3 `CreateBucket`/`PutObject` simulated allowed; existing Bedrock model calls already work under the current operator identity. Neither is a confirmed missing operator permission. The new runtime role still needs its own permissions.

## Scoped deployment prerequisites (not all independently tested)

- **Operator:** AgentCore `ListAgentRuntimes`, `GetAgentRuntime`, `CreateAgentRuntime`, `UpdateAgentRuntime`, `DeleteAgentRuntime`, `InvokeAgentRuntime`, `StopRuntimeSession`; endpoint create/get/list/update/delete if managing named endpoints; resource tagging if used. Restrict to demo resources where supported. Add `iam:PassRole` for the one execution role and service, artifact-prefix S3 read/write/list, and demo CloudWatch log read access.
- **Runtime execution role:** trust `bedrock-agentcore.amazonaws.com` with account/source restrictions; `bedrock:InvokeModel` for Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) and Nova Lite (`amazon.nova-lite-v1:0`); `secretsmanager:GetSecretValue` for the one Oracle secret; S3 artifact read; scoped CloudWatch log delivery. Add KMS decrypt only for a customer-managed key in use and telemetry permissions only if enabled. Administrator can provision log groups/policies in advance.
- **Packaging/network:** this implementation uses a Linux ARM64 ZIP, not ECR/CodeBuild, and needs no EC2 VM. Confirm Runtime-to-Oracle TCPS reachability. For VPC deployment, platform owners provide subnet/security-group configuration, routing/DNS and required AgentCore network service-linked-role provisioning. Workstation connectivity is not evidence of Runtime connectivity.
- **Quick:** subscription onboarding uses `quicksight:CreateAccountSubscription`; request subscription inspection, one-user registration/administration (`RegisterUser`, `DescribeUser`, `UpdateUser` as needed), and the in-product role needed to configure the demo MCP integration. Have the Quick administrator determine the integration-specific access after onboarding. Investigate SCPs, permission boundaries, federation and service prerequisites for the observed signup denial. No broad account-wide Quick administration is required for routine demo use.
- **EKS alternative:** namespace-scoped Kubernetes RBAC and cluster access for the demo, plus a platform-configured Pod Identity association or IRSA role. Pod Identity requires its agent and association permissions (including scoped `eks:CreatePodIdentityAssociation` and `iam:PassRole` for its role); IRSA instead needs OIDC trust. Cluster/worker creation, EC2 networking and service-linked roles are needed only if creating a new cluster. EKS is a separate experiment, not an AgentCore prerequisite.
- **Database, separately:** a least-privilege Oracle demo login/secret and approved read-only access. EKS identity requires an Oracle-supported SQL authentication path; AWS STS credentials alone are not Oracle database tokens. AWS grants cannot establish that support or create Oracle schema mappings.

## Who to ask

Send to the AWS account owner / IAM Identity Center permission-set administrator, copying the Quick subscription/billing owner and EKS platform owner for those portions. No verified individual or internal ticket queue is known. Ask for resource-scoped access or administrator provisioning, not AdministratorAccess. Include the account ID, assigned SSO permission sets and region in the private request.

## Official references

- [AgentCore runtime and execution-role permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)
- [Quick account subscription API](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_CreateAccountSubscription.html)
- [EKS Pod Identity association prerequisites](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-association.html)
