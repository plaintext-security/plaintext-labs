# Track 11 — Zero Trust Network Access

**The perimeter is dead; identity is the new control plane.** Replace "inside the network =
trusted" with per-request, identity-aware access — built with open source and cloud-native
tools.

## What you'll be able to do
- Explain Zero Trust and SASE beyond the marketing, and where each actually applies.
- Make identity and device posture the basis for access — with OSS tools and cloud-delivered services.
- Stand up identity-aware access with no inbound ports using both self-hosted and free managed options.
- Segment, express policy as code, and monitor a Zero Trust environment.
- Give workloads a cryptographic identity (SPIFFE/SPIRE) so services authenticate each other with mutual TLS, not network position.

## Modules

| # | Module | What you'll learn | OSS / free tools |
|---|--------|-------------------|--------------------|
| 01 | [Zero Trust Principles](modules/01-zero-trust-principles/README.md) | Why the perimeter failed; the core tenets and the SASE landscape | — |
| 02 | [Identity as the Control Plane](modules/02-identity-control-plane/README.md) | Authentication, SSO, and authorization; OIDC/SAML federation with enterprise IdPs | `keycloak` |
| 03 | [Device Trust & Posture](modules/03-device-trust-posture/README.md) | Tying access to device health; hardware-bound auth and network-level device trust | `tailscale`, `headscale`, FIDO2/passkeys |
| 04 | [ZTNA Architectures](modules/04-ztna-architectures/README.md) | OSS vs. cloud-delivered patterns and trade-offs | — |
| 05 | [SASE & Cloud-Delivered Zero Trust](modules/05-sase-cloud-delivered/README.md) | Managed ZT at the edge; when SASE beats self-hosted | Cloudflare Zero Trust (free tier) |
| 06 | [Identity-Aware Access](modules/06-identity-aware-access/README.md) | Per-request access with no open ports; self-hosted vs. managed | `pomerium`, `tailscale` |
| 07 | [Microsegmentation](modules/07-microsegmentation/README.md) | Limiting blast radius between workloads | `cilium` |
| 08 | [Policy as Code](modules/08-policy-as-code/README.md) | Continuous, versioned authorization | `OPA` |
| 09 | [Monitoring & Detection in Zero Trust](modules/09-monitoring-detection/README.md) | What "trust nothing" means for logging and detection | `sigma` |
| 10 | [Workload Identity & mTLS](modules/10-workload-identity-mtls/README.md) | Cryptographic service-to-service identity; mutual TLS keyed on identity | `SPIFFE`/`SPIRE` |

## Phases & projects

The ten modules run in three phases; each ends in a **project** that integrates its modules (a
phase is the substantial, standalone unit — a single module is a few hours). Identity-aware proxies
touch real access — test only against resources you own.

- **Phase 1 · Principles & identity** (01–03) — **Project:** stand up an identity control plane with
  Keycloak (OIDC/SAML) and tie access to device posture — passkeys/FIDO2 and a Tailscale/Headscale
  mesh — with a short written map of the Zero Trust tenets each control satisfies.
- **Phase 2 · Architectures & access** (04–06) — **Project:** publish a lab service with **no inbound
  ports** behind an identity-aware proxy — self-hosted (Pomerium/Tailscale) *and* cloud-delivered
  (Cloudflare Zero Trust) — and explain the trade-off you'd choose for which use case.
- **Phase 3 · Segment, govern & monitor** (07–10) — segment the network with Cilium, give each
  workload a cryptographic identity (SPIFFE/SPIRE) so service-to-service calls are mutually
  authenticated rather than trusted by position, govern with policy as code, and monitor it.
  **Project:** the track capstone — segment the workloads with Cilium, enforce authorization as code
  with OPA, and prove from the access logs that every request was authenticated and authorised —
  delivering the setup, the policy-as-code, and the audit trail.

## Prerequisites
Complete Track 00 — Foundations; Track 05 — Cloud helps.

> Build with your own accounts and lab hosts. Identity-aware proxies touch real access —
> test against resources you own.

## Capstone
Publish a lab service with **no inbound ports** behind an identity-aware proxy (Pomerium or
Cloudflare Tunnel + Access), enforce an access policy as code with OPA, and show the access
logs that prove every request was authenticated and authorised. **Deliverable:** the working
setup, the policy-as-code, and the audit trail.

The starter scaffold and acceptance checks live in
[`plaintext-labs/ztna/capstone/`](https://github.com/plaintext-security/plaintext-labs/tree/main/ztna/capstone).

### Capstone rubric

The service must be reachable with **no inbound ports**, gated by **policy as code**, with an
**audit trail that proves it**. **Proficient is the bar to ship.**

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **No inbound ports** | Service exposed on an open port | Service reachable only through an identity-aware proxy/tunnel; no inbound ports | Verified with an external port scan showing nothing open; egress-only tunnel proven |
| **Identity-aware access** | Single shared credential | Per-request access tied to authenticated identity (OIDC/SSO) | Device posture or hardware-bound auth (FIDO2/passkey) factored into the decision |
| **Policy as code** | Policy clicked in a UI | Access policy expressed as code (OPA/Rego) and version-controlled | Policy is tested — allow *and* deny cases asserted — and least-privilege by default |
| **Audit trail** | No logs, or logs don't show identity | Access logs prove each request was authenticated and authorised | A denied-and-allowed pair shown end to end; logs feed a detection |
| **Reproducibility** | Manual, undocumented setup | A reader can stand up the proxy and policy from the committed config | One command brings the whole gated service up; policy change is a reviewed diff |

## AI & automation
ZTNA is policy-as-code, and AI will happily write the policy — including one that's quietly
too permissive. The skill is reviewing generated authorization rules against least
privilege before they go live. AI drafts the policy; you prove it denies what it should.

## Standards & further reading
- NIST SP 800-207 (Zero Trust Architecture)
- CISA Zero Trust Maturity Model
- The BeyondCorp papers (Google)
- Gartner SASE framework overview
- Cloudflare Zero Trust documentation (free tier)
- Open Policy Agent and Pomerium documentation
