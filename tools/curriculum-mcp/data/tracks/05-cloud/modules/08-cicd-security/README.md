# Module 08 — CI/CD Pipeline Security

*Variant D · breach-driven, predict-the-injection-point → harden ("the pipeline was the attack surface"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *the build pipeline is the highest-trust path you own — and SolarWinds proved it's the least-watched one.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 07 — Secrets Management](../07-secrets-management/README.md)
{ .module-meta }


## The case

In December 2020, [FireEye disclosed](https://cloud.google.com/blog/topics/threat-intelligence/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor/)
that an attacker had been inside thousands of networks for most of a year — and that the front door was a
routine software update. SolarWinds' Orion network-management platform shipped a signed update containing
a backdoor the industry came to call **SUNBURST.** Roughly **18,000 organisations installed it**, including
US federal agencies; the [SEC's later enforcement order](https://www.sec.gov/files/litigation/admin/2023/34-98908.pdf)
and CISA's [Emergency Directive 21-01](https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise)
make the scope a matter of public record.

The detail that makes this *the* canonical pipeline breach is *where* the malware went in. The attacker did
**not** commit malicious code to SolarWinds' source repository — that would have shown up in review. They
compromised the **build system** and injected the backdoor *during compilation*, after the trusted source
had been checked out and before the trusted certificate signed the output. The result was a backdoored
binary carrying SolarWinds' **own legitimate code-signing signature** — valid, trusted, auto-installed.

So before you read on, this module turns on one question — the same one you'll ask of every pipeline you
ever review:

> **In the path from a developer's commit to a signed, deployed artifact, where does the attacker inject —
> and which step would have caught them?**

## Your job

By the end of this module you'll **predict the injection point** in a real pipeline, then *harden it where
the prediction lands.* You'll run the find-half (gitleaks for secrets, trivy for image CVEs, generate an
SBOM) over a sample pipeline, then do the build-half this module is really about: **write the hardened
GitHub Actions workflow** — pinned action SHAs, least-privilege OIDC tokens instead of long-lived secrets,
and **build provenance/attestation** so the artifact carries proof of *how* it was built, not just *who*
signed it. That hardened workflow is the deliverable, and it's a real artifact: it mirrors the
supply-chain hardening this very curriculum's repos shipped as task **T23** (pinning every Actions `uses:`
to a commit SHA + Dependabot).

## Call it before you read on

Don't scroll. Mark the path below at the point you think SUNBURST went in — and name the one control that
would have caught it there. Being wrong is the teaching event.

```
[dev commits] → [source repo / review] → [BUILD: compile, package] → [SIGN with cert] → [publish/deploy]
```

> **Q1.** At which arrow did the attacker inject the backdoor — and why does the popular guess ("they
> snuck bad code into the repo") miss?
>
> **Q2.** Orion's update was **signed with SolarWinds' real certificate** and the signature verified
> perfectly. What did that signature actually prove — and what did it *not* prove?
>
> **Q3.** Name one control that, present in the pipeline, would have made the injected build *fail to
> verify* downstream even though it was correctly signed.

## The injection point, revealed

Hold your answers against these.

**Q1 — the injection was in the build, between two things everyone trusted.** Most people guess the source
repo, because that's where we're trained to look — code review, branch protection, signed commits all
guard *that* arrow. SUNBURST walked past all of it by going in *after* checkout and *before* signing: the
attacker's tooling watched for Orion's build and swapped in the backdoored source during compilation, so
the artifact that came out the other side never matched anything a reviewer had seen. **The pipeline's
own most-privileged, least-watched stage — the build — was the attack surface.** This is the move that
separates someone who *audits* a pipeline from someone who *recites* "shift left": the dangerous gap isn't
the code, it's the **distance between trusted source and trusted signature**, and nothing in a normal
pipeline was watching that distance.

**Q2 — signing proves WHO built it, not WHAT they built.** This is the mental model to keep for the rest
of your career. A code-signing certificate is an identity claim: "an artifact bearing this signature came
from the holder of this key." SolarWinds held the key; the build server had legitimate access to use it;
the signature was genuine. What the signature could *not* attest is that the bytes it signed corresponded
to the reviewed source — because the signing step trusts whatever the build step hands it. **Signing
authenticates the signer; it says nothing about the integrity of the build process that produced the
input.** Every downstream check that "verified the signature and trusted the binary" was answering the
wrong question. The missing link SUNBURST exposed is **build provenance** — a tamper-evident statement of
*how, from what source, by which builder* an artifact came to be. Trust the build, not just the signature.

**Q3 — provenance/attestation as the gate is the control that breaks the chain.** This is what
[SLSA](https://slsa.dev/spec/v1.0/about) (Supply-chain Levels for Software Artifacts) was built to answer.
If the pipeline emits a signed **provenance attestation** — produced by the build platform itself,
recording the source commit, the builder identity, and the materials — then a consumer can demand "show me
provenance from a hardened builder, tied to *this* commit" *before* installing. A backdoor injected at the
build step either can't produce matching provenance (the builder wasn't the trusted one, the source digest
doesn't match) or the tampering is detectable in the attestation. The signature alone passes; **the
attestation is the gate that fails the SolarWinds build.** That, plus pinning every dependency and action
to an immutable digest (so a re-pointed tag can't quietly change what runs) and minting **OIDC tokens**
instead of long-lived secrets (so a compromised build can't exfiltrate a standing credential), is the
hardened pipeline — and it's exactly the shape of T23's Actions-hardening work in this repo.

## Learn (~4 hrs)

*Richer than a foundations module: the pipeline is the integration point for everything you've built, so
it curates the supply-chain spine in depth. Read the case above first.*

**The breach, from primary sources (~1 hr)**
- [Mandiant/FireEye — "Highly Evasive Attacker Leverages SolarWinds Supply Chain" (SUNBURST writeup)](https://cloud.google.com/blog/topics/threat-intelligence/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor/) (~30 min) — the discovering researcher's technical anatomy of the backdoor and the build-time injection. Read for *where* and *how* it went in.
- [CISA — Emergency Directive 21-01 (Mitigate SolarWinds Orion Code Compromise)](https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise) (~15 min, skim) — the federal response; orient on scope and the "trusted update" framing.
- [SEC — Litigation Release: SolarWinds Corporation and Timothy G. Brown](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-25887) (~15 min, skim) — the primary regulatory record of the alleged build-environment and disclosure failures (the SEC's first cyber-disclosure fraud charges against a company and its CISO).

**The fix — provenance, pinning, OIDC (~2 hrs)**
- [SLSA v1.0 — "About" and the provenance model](https://slsa.dev/spec/v1.0/about) (~30 min) — the framework that names the missing link: build provenance levels. Read "About" and the provenance concept; that's the WHAT-not-WHO model made concrete.
- [GitHub — Security hardening for GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use) (~40 min) — the authoritative guide: expression injection, minimal `permissions`, pinning actions to SHAs, OIDC. Read the whole page; it's the checklist your hardened workflow satisfies.
- [GitHub — about artifact attestations / build provenance](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds) (~20 min) — how Actions emits a signed provenance attestation you can verify before deploy.
- [trivy — vulnerability scanning + SBOM](https://aquasecurity.github.io/trivy/latest/docs/scanner/vulnerability/) (~20 min) — how trivy scans an image and emits a CycloneDX SBOM; read "Container Image" and SBOM sections.

**Secrets & injection in the pipeline (~1 hr)**
- [gitleaks — gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) (~20 min) — `detect` vs `protect`, the `.gitleaks.toml` custom-rule format, the CI gate pattern.
- [MITRE ATT&CK T1195.002 — Compromise Software Supply Chain](https://attack.mitre.org/techniques/T1195/002/) (~15 min) — the technique SUNBURST instantiates; pair it with T1552 (unsecured credentials) for the secrets surface.

## Key concepts
- The build step — between trusted source and trusted signature — is the highest-trust, least-watched stage; that distance is the attack surface (SUNBURST went in *there*, not in the repo)
- **Signing proves WHO built it, not WHAT they built** — a valid signature on a backdoored binary; build provenance/attestation is the missing link
- SLSA provenance as a *gate*: demand a signed attestation tying the artifact to its source + builder before deploy — it fails the SolarWinds build even though the signature passes
- Pin every action/dependency to an immutable digest (SHA), not a mutable tag — a re-pointed tag silently changes what runs (this repo's T23)
- Least-privilege pipeline auth: short-lived **OIDC** tokens over long-lived secrets, minimal per-job `permissions:`, sanitised `${{ }}` expressions (no expression injection)
- The find-half (gitleaks, trivy, SBOM) is necessary but not sufficient — it scans inputs; provenance attests the *process*

## AI acceleration
GitHub Actions YAML is an excellent AI-review target: paste a workflow and ask the model to flag injection
points, excessive `permissions`, and unpinned `uses:` references — it pattern-matches these well, and it
will draft a hardened rewrite fast. Two things it reliably gets wrong, and they're exactly this module's
lesson. First, it treats a green signature/scan as "secure" and rarely volunteers **provenance** — because
"who signed it" is the question everyone trains on; you must direct it to add attestation as the gate.
Second, it misses **multi-job data-flow injection** where a compromised early step passes tainted data to a
later privileged one. Have the model draft; you own the verdict — confirm the hardened workflow actually
*fails the SolarWinds-shaped build*, not just passes the linters.
