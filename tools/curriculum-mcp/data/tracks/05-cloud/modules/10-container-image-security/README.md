# Module 10 — Container & Image Security

*Variant D · breach-driven, predict-then-reveal verdict ("it runs — what else is in it?"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *a container image is a tarball of someone else's decisions; "it works" and "it's clean" are orthogonal.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 08 — CI/CD Pipeline Security](../08-cicd-security/README.md)
{ .module-meta }


## The case

Between mid-2017 and mid-2018, a Docker Hub account named **`docker123321`** quietly published a set
of public images under the names of software people pull every day — `cron`, `tomcat`, `mysql`. They
worked. You could pull `docker123321/cron`, run it, and get a working cron. What you also got, baked
into the layers, was an **XMRig Monero miner and, in cases Kromtech traced, an embedded reverse
shell**. The campaign ran for roughly **ten months** before Fortinet published on it and Docker pulled
the images on 10 May 2018. By then `docker123321/cron` alone had been pulled **over a million times**,
the family **over five million**, and the actor had mined ~**$90,000** in Monero on other people's
compute. Documented in
[Kromtech's writeup](https://kromtech.com/blog/security-center/cryptojacking-invades-cloud-how-modern-containerization-trend-is-exploited-by-attackers)
and [Fortinet's threat research](https://www.fortinet.com/blog/threat-research/yet-another-crypto-mining-botnet).

Three years later, the same logic ran in reverse. In the **Codecov 2021** breach
([Codecov's own post-mortem](https://about.codecov.io/apr-2021-post-mortem/)), the attacker's *entry
point* was a credential **left in a layer of one of Codecov's public Docker images** — extracted, used
to alter the Bash Uploader, and exfiltrate the CI secrets of thousands of downstream projects. One
image leaked a key *out*; the `docker123321` images smuggled malware *in*. Both are the same class of
failure, and both turned on a single fact: **a container image is opaque, and "it runs" tells you
nothing about what else is dormant in its layers.** So this module turns on one question:

> **This image runs your app perfectly in testing. What ELSE is in it?**

## Your job

By the end of this module you'll **call what's hidden in a working image, then prove it** — scan with
`trivy` and `grype`, triage CVEs by *fixability* (the load-bearing judgment, not the count), and audit
the Dockerfile for the hygiene failures a scan-for-CVEs misses. Then you do the half a scan-and-triage
skips: **author a hardened multi-stage rebuild — minimal/distroless base, no build tools in the final
layer, secrets out of the image, base pinned by digest — and prove the rebuild measurably cuts the
attack surface.** Finally you encode the verdict as a **CI scan gate** that fails the bad image and
passes the rebuild. That loop — what's dormant → prove it → rebuild it clean → make it un-recurrable —
is the exact motion of a container-security review.

## Call it before you read on

Don't scroll. An image you pulled builds, the app's tests are green, it serves traffic. Write your gut
answers — being wrong is the point.

> **Q1.** You wrote zero of the vulnerable code; your `FROM python:3.8-slim` base "just works." Whose
> CVEs are you now shipping, and how many — roughly none, a handful, or dozens?
>
> **Q2.** A `trivy image` scan comes back clean of HIGH/CRITICAL CVEs. Does that mean the image is
> safe to ship?
>
> **Q3.** The image runs and passes every test. What can `docker history` / a layer scan still reveal
> that *running the container* never would?

## The verdict, revealed

Hold your answers against these.

**Q1 — you inherit everyone above you in the `FROM` chain.** An image tagged `python:3.8-slim` is a
frozen snapshot of a Debian root filesystem plus a Python install plus *their* transitive packages —
`curl`, `libssl`, `glibc`, dozens more you never named. The moment you write `FROM`, **their CVEs
become your CVEs**, and you ship them whether you read them or not. Worse, **tags are mutable; the bits
behind them aren't.** `python:3.8-slim` pulled today and the same tag pulled last year are different
digests, and a container started from a cached old digest runs old, vulnerable bits forever. Scanners
(`trivy`, `grype`) work by extracting the image's **software bill of materials** — every package and
version — and matching it against CVE feeds (NVD, GitHub Advisory, distro advisories). The naive guess
("I wrote clean code, so my image is clean") is exactly backwards: the supply-chain risk lives in the
base and package layers you *didn't* write, and a typical slim base will surface **dozens** of CVEs on
a fresh scan. You're not auditing your code; you're auditing **someone else's decisions, inherited.**

**Q2 — "no fixable HIGH/CRITICAL" is the answer, and even that isn't "safe."** Two traps live here.
First, the count is a distraction; **fixability is the verdict.** A Critical CVE with no patch yet
available is something you *track*, not something you can fix today — gating your pipeline on it just
blocks every build for no action. A High with a fixed version in the distro's repo means **rebuild
now.** The right gate is severity-*and*-fixable (`--exit-code 1 --severity HIGH,CRITICAL`, ignoring
unfixed), not raw severity. Second — and this is the `docker123321` lesson — **CVE scanning answers
"are the packages patched," not "is anything malicious or wrong in here."** A clean CVE report says
nothing about an embedded miner, a planted reverse shell, a secret in a layer, an extra binary, or a
container that runs as root with a debug port open. "It scanned clean" and "it's clean" are not the
same claim.

**Q3 — the layers remember what the running container hides.** This is the `docker123321`/Codecov
heart. A running container shows you the *intended* process; the **image layers** show you everything
ever added, including things deleted in a later layer (still recoverable) and credentials baked into an
`ENV` or `ARG` (readable by anyone with registry access via `docker history` / `docker inspect`).
That's literally how Codecov's attacker got in: a key sitting in a published layer. So the second half
of image security isn't CVE counting at all — it's **hygiene and provenance**: does it run as a
non-root `USER`; is the base pinned to a digest you can audit, not `latest`; are secrets injected at
*runtime* instead of baked in; is the final layer free of build tools, package managers, and shells an
attacker could pivot through? `trivy config` and `hadolint` catch this configuration class that a CVE
scan walks right past.

**The fix is a rebuild, not a patch.** You can't `apt upgrade` your way out of an inherited base — you
**rebuild from a minimal, current, pinned base.** A multi-stage build does the work in a fat "builder"
stage and copies *only the artifact* into a tiny final stage (distroless or `-slim`), so the build
tools, package manager, and shell that an attacker would use never ship. Fewer packages → smaller SBOM
→ fewer inherited CVEs → smaller blast radius, all at once. **"It works" and "it's clean" are
orthogonal axes; the rebuild is how you move on the second one without losing the first.**

## Learn (~3 hrs)

*Curate the scanner mechanism; the trust argument above is the spine. Read the case first.*

**The supply-chain anchor in the practitioner's words (~30 min)**
- [Kromtech — Cryptojacking invades the cloud (the `docker123321` campaign)](https://kromtech.com/blog/security-center/cryptojacking-invades-cloud-how-modern-containerization-trend-is-exploited-by-attackers) (~15 min) — the discovering researcher's writeup; read for *how a working image hides a miner + reverse shell* and the pull counts.
- [Codecov — April 2021 post-mortem](https://about.codecov.io/apr-2021-post-mortem/) (~10 min) — first-party RCA; note the entry point was *a credential in a Docker image layer*, and that the remediation was "squash / convert public images to multistage." The fix is this module.

**Scanning: SBOM, severity, and fixability (~1 hr)**
- [Trivy — Filtering scan results](https://trivy.dev/docs/latest/configuration/filtering/) (~30 min) — official docs; read the "By Severity" and "By Status" (`--ignore-unfixed`) sections so the **fixable-vs-unfixable** judgment is concrete, not abstract.
- [Anchore Grype — README & supported ecosystems](https://github.com/anchore/grype) (~15 min) — skim how Grype's DB sources differ from Trivy's; the lab runs both because **one scanner is one opinion.**
- [NVD — CVSS v3.1 scoring](https://nvd.nist.gov/vuln-metrics/cvss) (~15 min, orient) — read the Base-Score vectors (AV/AC/PR/UI) so you can say "Critical in theory, unreachable in this context."

**Hardening the artifact (~1 hr)**
- [Docker — Multi-stage builds](https://docs.docker.com/build/building/multi-stage/) (~20 min) — the mechanism for shipping only the artifact, not the toolchain. This is the graded rebuild.
- [GoogleContainerTools — distroless](https://github.com/GoogleContainerTools/distroless) (~15 min) — read the README's rationale: no shell, no package manager, minimal CVE surface — *why* the final stage should be near-empty.
- [OWASP — Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) (~20 min) — maps one-to-one onto the `Dockerfile.bad` findings: non-root `USER`, no secrets in layers, pinned base, no `--privileged`.

## Key concepts
- `FROM` inherits the base's CVEs *and* its trust — you ship someone else's decisions whether you read them or not
- Tags are mutable, digests are immutable: pin `@sha256:...` and rebuild on a schedule, don't trust a tag
- **Fixability, not count, is the verdict** — fixable HIGH/CRITICAL = rebuild now; unfixed = track; gate on severity-*and*-fixable
- "Scanned clean of CVEs" ≠ "clean": miners, reverse shells, secrets-in-layers, and root/`--privileged` config all pass a CVE scan
- Image *layers* remember what the running container hides — `docker history`/`inspect` reveal baked-in secrets and deleted files
- The fix is a **multi-stage rebuild to a minimal/distroless base**, not a patch — ship the artifact, not the toolchain
- One scanner is one opinion: run `trivy` and `grype` and reconcile
- MITRE ATT&CK T1195.002 — Supply Chain Compromise: Compromise Software Supply Chain

## AI acceleration
Paste your `trivy image --format json` output and `docker history` into a model and ask it to rank the
findings by exploitability for *your* workload (e.g. internet-facing API, non-root). It's a strong
first-pass triage — good at ordering by fixability and proposing the minimum base upgrade that closes
the most CVEs. But it sees the SBOM, not the call graph: it **cannot tell you whether the vulnerable
code path is actually reachable** from your application, and it will not flag a planted miner or a
secret-in-a-layer that a CVE feed doesn't list. Treat its ranking as a hypothesis; you own the
reachability call before you file a remediation ticket, and you own the rebuild. AI drafts → you review
→ you ship it.
