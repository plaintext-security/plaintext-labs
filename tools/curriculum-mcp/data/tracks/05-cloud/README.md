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
| 17 | [Data Protection & KMS](modules/17-data-protection-kms/README.md) | Envelope encryption; key policies & separation of duties | `aws-kms`, `openssl` |

## Phases & projects

The sixteen modules run in three phases; each ends in a **project** that integrates its modules (a
phase is the substantial, standalone unit — a single module is a few hours).

- **Phase 1 · Identity, posture & the pipeline** (01–08) — **Project:** audit a deliberately
  vulnerable account (CloudGoat/flaws.cloud) with `prowler`/`pmapper` to map an IAM privilege-escalation
  path, then close it as Terraform gated by `checkov`/`trivy` in CI, with secrets pulled out of code and
  into a broker.
- **Phase 2 · Containers & Kubernetes** (09–13) — **Project:** harden a workload end to end — scan the
  image, lock down a serverless execution role, demonstrate a container breakout caught by Falco, and
  enforce RBAC, NetworkPolicy, and an admission policy as code on a kind cluster.
- **Phase 3 · Attack, detect & respond** (14–16) — **Project:** the track capstone — simulate a cloud
  attack with `stratus-red-team`/`pacu`, detect it from cloud logs (native detector *and* a Sigma rule),
  and investigate-and-contain it — delivering the attack path, the fix-as-code, and the detection.

## Prerequisites
Complete Track 00 — Foundations first.

> Labs use your own free-tier accounts or intentionally vulnerable environments (CloudGoat,
> flaws.cloud). Never test accounts or tenants you don't own, and tear down billable
> resources when done.

## Capstone
The capstone is the Phase 3 project — it integrates all three phases. Run the full cloud-attack loop
against a deliberately vulnerable account: **simulate** a real attack (`stratus-red-team` / Pacu),
**detect** it from cloud logs (a native detection *and* a Sigma rule), then **investigate and
contain** it — and close the underlying path as Terraform gated by a scanner in CI (the IAM-and-posture
work from Phases 1–2). **Deliverable:** the attack path, the fix-as-code, and the detection.

The starter scaffold and acceptance checks live in
[`plaintext-labs/cloud/capstone/`](https://github.com/plaintext-security/plaintext-labs/tree/main/cloud/capstone).

### Capstone rubric

The loop is **attack → fix-as-code → detect**, and the fix must be *gated*, not just written.
**Proficient is the bar to ship.**

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Attack path** | A single misconfig noted, no chain | An IAM/serverless privesc path walked end to end and explained | Multi-step chain mapped to ATT&CK for Cloud, with the trust relationship that enabled each hop |
| **Fix as code** | Fixed in the console (click-ops) | The fix expressed as Terraform/IaC that closes the path | Least-privilege fix, parameterised and reusable, with the diff that proves the path is gone |
| **CI gate** | No scanner, or scanner not enforced | A scanner (Checkov/tfsec/Trivy) runs in CI and *fails* the bad config | The gate is tuned (no noise), blocks merge on the specific finding, and passes on the fix |
| **Detection** | No detection, or fires on nothing | A detection from cloud logs (CloudTrail/equivalent) that catches the attack | Detection validated against benign activity for false positives, mapped to the technique |
| **Cost & teardown** | Left billable resources running | Resources torn down; no secrets in code | Whole thing rebuilds from `terraform apply` and tears down cleanly; budget-safe by design |

## AI & automation
In the cloud the infrastructure *is* code, and increasingly that code is AI-written —
exactly where misconfigurations hide (over-broad IAM, `0.0.0.0/0`, privileged containers).
The posture this track drills: **AI authors → you review → scanners gate → you own it.**

## Standards & further reading
- CIS Benchmarks for AWS/GCP/Azure and Kubernetes
- MITRE ATT&CK for Cloud and Containers
- Cloud provider Well-Architected / security best-practice guidance
- OWASP Kubernetes and Cloud-Native security guidance
