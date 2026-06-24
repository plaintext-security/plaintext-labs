# Module 03 — Device Trust & Posture

*Type 7 · Build-&-Operate — stand up a working device-identity mesh, enroll a device, and prove access is bound to that device; the deliverable is the running, reviewed system, not an essay. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *identity tells you who is asking; device trust binds the answer to a known, healthy machine — so a stolen credential alone is not enough.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Identity as the Control Plane](../02-identity-control-plane/README.md)
{ .module-meta }

## Why this matters

In August 2022, an attacker compromised the **personal home computer of a senior LastPass DevOps
engineer** — one of only four people with decryption access to the company's vault backups. The
entry point was not LastPass's network. It was a **Plex Media Server the engineer ran at home**, left
unpatched against a vulnerability (CVE-2020-5741) that Plex had fixed *two years earlier*. The
attacker landed on the machine, installed a keylogger, and captured the engineer's master password —
**after** the engineer had already passed MFA. With that credential, between September 8 and 22 the
attacker reached LastPass's **AWS S3 backups** and exfiltrated encrypted customer vault data. The
unauthorized access ran for 79 days before AWS GuardDuty flagged it.

Read the failure precisely, because it is the case for this entire module: **identity verification
worked, and it was not enough.** The right human, the right credential, even MFA — all satisfied. What
was never asked was *"is the device this is coming from one we trust?"* An unmanaged home machine,
outside any patch policy or endpoint visibility, was allowed to become the trusted launch point into
cloud backups. A stolen credential on a healthy, enrolled, fully-patched corporate laptop is a serious
incident; the **same credential on an unmanaged, compromised personal box is the LastPass breach.** A
model that only verifies identity cannot tell those two apart. Device trust is the second pillar of
Zero Trust after identity, and it is the pillar most organizations handle worst.

## The core idea

Device trust has two halves, and they answer two different questions. **Is this the device I think it
is? (identity)** and **is this device in a state I'm willing to trust? (posture).** This module builds
the first half end-to-end and is honest about why the second half stays mostly conceptual in a
self-hosted lab.

**Device identity is cryptographic, not network-positional.** The old model trusted a device by where
it sat — if the request came from the corporate `/20`, it was "inside" and therefore trusted. IPs are
trivially spoofed and say nothing about the machine. The modern answer is a **private key generated on
the device** (ideally in a TPM or Secure Enclave so it can't be exported) whose public half is
registered with a coordination plane. **WireGuard/Tailscale is the clearest concrete instance:** each
device generates a WireGuard keypair, registers the public key, and *every* packet thereafter is
authenticated by that key. WireGuard's crypto is fixed by design (Noise framework, ChaCha20-Poly1305,
Curve25519) — no algorithm negotiation to downgrade, no legacy cipher suites to misconfigure; a peer
is *only* a 256-bit public key. The coordination server you'll run, **headscale** (the self-hosted
Tailscale control server), is the configuration plane: it distributes public keys and enforces ACLs.
It is **not** the data plane — once keys are exchanged, traffic flows peer-to-peer. The load-bearing
consequence for the lab: a machine without the registered private key **cannot join the mesh**, so an
unenrolled device is denied by construction, not by a rule someone remembered to write. That is the
thing you'll prove.

**The one judgment that makes this good ZT, not just a VPN: default-deny on the ACL.** A WireGuard
mesh that lets every enrolled device reach everything is just a flatter network with better crypto —
you've moved the perimeter, not removed it. Zero Trust requires that the ACL *start* from deny and
only allow the specific tag-to-service edges the architecture needs (`tag:corp-managed` can reach
`tag:target`; an untagged or contractor device cannot). The failure mode to watch for — and the thing
AI-generated ACLs reliably get wrong — is an **implicit default-allow**: a policy that looks correct,
passes syntax, and quietly grants everything it didn't explicitly deny. You verify against it the only
honest way: by confirming an *unenrolled* device is refused, not merely that an enrolled one succeeds.

**Posture is the second half, and self-hosting can't fully prove it — so we say so.** Even a genuinely
identified device can be *unhealthy*: 60 days behind on patches, EDR disabled, disk unencrypted — the
LastPass home machine, exactly. Production ZT gates on this: Cloudflare Access queries a CrowdStrike
Zero Trust Assessment score, OS version, and disk-encryption state before issuing access; Tailscale's
tag/group ACLs segment "managed corporate" from "contractor BYOD" inside one mesh. But those signals
come from a managed-endpoint stack (MDM, EDR) you cannot stand up for free in a container. So this
module is honest about the seam: you'll **build and prove device *identity***, and treat device
*posture* as **assessed from a structured policy** (`device-posture-policy.json`) mapped to the
controls a production deployment enforces — labelled as assessed, never as demonstrated. Closing that
seam with a real posture signal is what production EDR/MDM buys you; naming it is the practitioner's
job. (**FIDO2/passkeys** are the human-layer complement — a hardware-bound assertion proving *the user
is present at this device*, private key never leaving the authenticator. WireGuard proves the device;
FIDO2 proves the user on it; together they are NIST 800-207 Tenet 3. Because FIDO2 hardware is
physical, the lab exercises it via the browser at WebAuthn.io and reasons about it in prose.)

## Learn (~4 hrs)

**WireGuard and mesh networking (~1.5 hrs)**
- [WireGuard whitepaper](https://www.wireguard.com/papers/wireguard.pdf) (~40 min) — Donenfeld's original paper; read sections 1–3 (introduction, crypto model, protocol). Short but dense — it explains *why* WireGuard's fixed crypto model is a security advantage over IPSec/IKEv2 rather than a limitation.
- [Tailscale — How Tailscale Works](https://tailscale.com/blog/how-tailscale-works) (~30 min) — the clearest explanation of the coordination-server / data-plane split, NAT traversal, and the ACL model. Read it to understand exactly what headscale is doing in the lab.

**headscale — the self-hosted control server (~30 min)**
- [headscale documentation](https://headscale.net/stable/) (~30 min) — the control server the lab runs. Read "Getting started" and the ACL section; the rest is operational reference for later.

**Device posture and ZT (~1 hr)**
- [Cloudflare Zero Trust — Device posture checks](https://developers.cloudflare.com/cloudflare-one/reusable-components/posture-checks/) (~30 min) — how a production product queries CrowdStrike, Intune, and OS-level signals to gate application access. This is what the lab's `device-posture-policy.json` stands in for, and what you cannot self-host for free.
- [Tailscale — Access controls (ACLs)](https://tailscale.com/kb/1018/acls) (~30 min) — how to express "only devices tagged `corp-managed` can reach service X" in HuJSON. Directly applicable; read it before you extend the lab's ACL.

**FIDO2 and passkeys (~1 hr)**
- [WebAuthn.io](https://webauthn.io/) (~20 min) — browser-based FIDO2/WebAuthn demo; register and authenticate with your built-in authenticator, no hardware needed. Run it to feel the challenge-response flow before the spec.
- [FIDO Alliance — Passkeys](https://fidoalliance.org/passkeys/) (~40 min) — the foundational explainer: authenticator binding, user verification, and why the private key never leaves the device. Read it for the "FIDO2 proves the user on the device" half of Tenet 3.

## Key concepts

- **Identity ≠ enough.** LastPass-2022: right user, right credential, MFA passed — and an unmanaged compromised device still became the trusted launch point into cloud backups.
- **Cryptographic device identity** — the WireGuard public key *is* the device's identity (vs. spoofable IP/VLAN trust); no registered private key, no membership in the mesh.
- **Control plane vs. data plane** — headscale distributes keys and enforces ACLs; WireGuard tunnels carry traffic peer-to-peer, no central chokepoint.
- **Default-deny ACL is the ZT judgment** — an enrolled-can-reach-everything mesh is just a flatter VPN; the win is the tag-to-service allow-list, and the trap is the implicit default-allow.
- **Posture is assessed, not demonstrated, when self-hosted** — patch level / EDR / disk encryption come from EDR/MDM you can't run for free; the lab maps a structured policy to production controls and labels it honestly.
- **FIDO2/passkeys** — user-presence + hardware-bound credential; WireGuard proves the device, FIDO2 proves the user on it (NIST 800-207 Tenet 3).

## AI acceleration

A model will generate headscale/Tailscale ACL HuJSON from a plain-English description of your access
requirements, and it handles the syntax well — this is genuinely fast. The posture holds: **AI authors
→ you review every line → you own it**, and here the review has one concrete shape. An ACL that *looks*
correct can carry an **implicit default-allow** — the exact opposite of Zero Trust, and the single
failure a syntax check will never catch. So your review job is not "does it parse" but "does an
*unenrolled* or *untagged* device get refused." Prove it the only honest way: construct a `curl` from a
container with no registered keypair and confirm it cannot reach the protected service. If a device you
never tagged can still reach it, the ACL has a hole — and the model's confident, valid-looking output
was wrong. You direct it; you own the deny.
