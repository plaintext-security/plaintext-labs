# Track 05 — Cloud & Container Security

**Attack and defend cloud-native environments,** and express security as code — because in
the cloud the infrastructure *is* code. AWS/GCP/Azure plus containers and Kubernetes.

## What you'll be able to do
- Reason about shared responsibility, cloud identity, network controls, and trust.
- Find and explain privilege-escalation paths through IAM and serverless execution roles.
- Audit posture and infrastructure-as-code for misconfigurations, gated in CI.
- Secure containers and Kubernetes, and detect and respond to cloud attacks using both open tools and native cloud services (GuardDuty, Defender for Cloud, GCP SCC).

## Modules

| # | Module | What you'll learn | OSS / free tools |
|---|--------|-------------------|-----------------|
| 01 | [Cloud Fundamentals & Shared Responsibility](modules/01-cloud-fundamentals/README.md) | The model, accounts, and CLIs | cloud CLIs |
| 02 | [Cloud Identity & IAM](modules/02-cloud-identity-iam/README.md) | Policies, roles, trust, and federation | `cloudfox` |
| 03 | [IAM Attack Paths](modules/03-iam-attack-paths/README.md) | Finding privilege-escalation chains | `pmapper`, `cloudfox` |
| 04 | [Cloud Network Security](modules/04-cloud-network-security/README.md) | VPCs, Security Groups, PrivateLink, WAF, and flow logs | `cloudmapper`, cloud CLIs |
| 05 | [Posture & Misconfiguration Auditing](modules/05-posture-auditing/README.md) | Benchmarking accounts against known issues | `prowler`, `scoutsuite` |
| 06 | [Infrastructure-as-Code Security](modules/06-iac-security/README.md) | Scanning Terraform before it deploys | `checkov`, `tfsec`, `trivy` |
| 07 | [Secrets Management & Detection](modules/07-secrets-management/README.md) | Storing and finding leaked credentials | `vault`, `trufflehog` |
| 08 | [CI/CD Pipeline Security](modules/08-cicd-security/README.md) | Securing the path from commit to deploy | `trivy`, `gitleaks` |
| 09 | [Serverless Security](modules/09-serverless-security/README.md) | Function execution roles, event-injection, and confused deputy | `cloudfox`, `pacu`, `aws-sam-cli` |
| 10 | [Container & Image Security](modules/10-container-image-security/README.md) | Image hygiene and supply-chain scanning | `trivy`, `grype` |
| 11 | [Container Escape & Runtime](modules/11-container-escape-runtime/README.md) | Breakouts and runtime visibility | `falco` |
| 12 | [Kubernetes — RBAC & Network Policy](modules/12-kubernetes-rbac-network/README.md) | Least privilege and segmentation as code | `kube-bench` |
| 13 | [Kubernetes — Admission & Runtime](modules/13-kubernetes-admission-runtime/README.md) | Policy enforcement and runtime detection | `kyverno`, `falco` |
| 14 | [Cloud Attack Techniques](modules/14-cloud-attack-techniques/README.md) | Exploiting misconfig; simulating safely | `pacu`, `stratus-red-team` |
| 15 | [Cloud Logging & Detection](modules/15-cloud-logging-detection/README.md) | Native detectors vs. open tools; tuning signal | `falco`, `sigma`; GuardDuty / Defender for Cloud / GCP SCC |
| 16 | [Cloud Incident Response](modules/16-cloud-incident-response/README.md) | Investigating and containing in the cloud | `cloudtrail`, `hayabusa` |

## Prerequisites
Complete Track 00 — Foundations first.

> Labs use your own free-tier accounts or intentionally vulnerable environments (CloudGoat,
> flaws.cloud). Never test accounts or tenants you don't own, and tear down billable
> resources when done.

## Capstone
Find a privilege-escalation path in a deliberately vulnerable cloud account (CloudGoat or
flaws.cloud), explain it, then close it as code — Terraform gated by a scanner in CI — and
detect the attack from cloud logs. **Deliverable:** the attack path, the fix-as-code, and
the detection.

## AI & automation
In the cloud the infrastructure *is* code, and increasingly that code is AI-written —
exactly where misconfigurations hide (over-broad IAM, `0.0.0.0/0`, privileged containers).
The posture this track drills: **AI authors → you review → scanners gate → you own it.**

## Standards & further reading
- CIS Benchmarks for AWS/GCP/Azure and Kubernetes
- MITRE ATT&CK for Cloud and Containers
- Cloud provider Well-Architected / security best-practice guidance
- OWASP Kubernetes and Cloud-Native security guidance
