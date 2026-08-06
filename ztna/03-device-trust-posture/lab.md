# Lab 03 — Device Trust: bind access to the device, not the credential

> **Hands-on lab.** Environment: `plaintext-labs/ztna/03-device-trust-posture`.
> Objective: **stand up a headscale + WireGuard device-identity mesh and prove access is bound to an
> enrolled device — an off-mesh device is denied.** Target: **~60–90 min**, one finish line. This is a
> **container lab:** `make up` / `make demo` / `make down`.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Identity worked in LastPass — it wasn't enough.** | Right user, right master password, MFA passed; the *device* (unpatched home PC) was never questioned. **T1078 Valid Accounts.** |
| 2 | **Device identity is a key, not an IP.** | The WireGuard pubkey *is* the device; no registered key → no mesh membership → denied by construction. |
| 3 | **Control plane ≠ data plane.** | headscale distributes keys + ACLs; WireGuard carries traffic peer-to-peer. Two different jobs. |
| 4 | **Default-deny is the ZT judgment.** | An enrolled-reaches-everything mesh is a flatter VPN. The win is the tag→service allow-list; the trap is the implicit default-allow. |
| 5 | **Prove the *deny*, not just the allow.** | An off-mesh container reaching the target means the boundary is a hole — a syntax check never catches that. |
| 6 | **Posture is *assessed*, not demonstrated here.** | Patch/EDR/disk-encryption come from MDM/EDR you can't self-host free. Map the policy to production controls; label it honestly. |

*(If you can explain all six cold at the end — especially #1 and #5 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [two halves of device trust](README.md#the-two-halves-of-device-trust) and the
> [posture-gate diagram](README.md#3-posture-is-the-second-half-assessed-not-demonstrated).

---

## Warm-up — answer before you touch the mesh (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. LastPass: identity verification *passed*. Name the **one question** the access model never asked —
   and the two properties of the engineer's home machine that made its absence fatal.
2. A WireGuard mesh where every enrolled device can reach every service — what Zero-Trust property is
   still missing, and what's the name of the trap an ACL falls into when it forgets it?

---

## Setup

The environment lives in the companion `plaintext-labs` repo. It runs three containers: **headscale**
(the control server), **target-service** (nginx — the protected resource, *not* published on the host),
and **node** (a stand-in for an enrolled device).

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/03-device-trust-posture
make up        # start headscale + target-service + node; waits for headscale ready
make demo      # create the corp user + pre-auth key, fetch the target from the node
make down      # stop when done   (make reset = also drop volumes/images)
```

> **▸ On track if:** `make up` ends with `headscale is ready.`, `Headscale admin API :
> http://localhost:8088`, and `Target service : NOT exposed on host (only reachable via mesh)`.
> Hitting `http://localhost:8088` from your laptop reaches **headscale**; there is **no** host port for
> the target — that's the point.

> **Authorization note.** This lab probes only the containers it ships. Only ever run access probes
> against systems you own or have explicit written permission to test.

---

## Build it — read a little, do a little

### Step 1 — Run the demo and read what the control plane actually did

??? note "Concept (30 sec)"
    Flight-card #3. `make demo` exercises the **control plane**: it creates a headscale *user* (`corp`)
    and issues a **pre-auth key** — the token a real device would present to register its WireGuard
    pubkey. The `node` container is a **data-plane stand-in**: it reaches the target over shared Docker
    networking, standing in for the peer-to-peer WireGuard tunnel a registered client would build. So
    `headscale nodes list` stays empty — you're seeing the registration *machinery*, not a live
    tailscale client.

**Do it:** run `make demo` and read every section it prints.

> **▸ On track if:** the banner reads `Lab 03 — Device Trust Demo: headscale + WireGuard`; you see
> `--- Step 1: Create a headscale user (namespace) for Corp ---`, a printed `Pre-auth key: <token>`,
> a `headscale nodes list` table, and the `node` fetching the target — the HTML titled
> **`Corp — Internal Service`** with `Status: OK`. The closing block asks the key question: what
> happens to a container with **no** mesh membership?

### Step 2 — Prove access from the enrolled device

??? note "Concept (30 sec)"
    Flight-card #2. The node reaches the target because it is **on the mesh** (here: on `ztna-net`),
    not because of its IP. In production the same edge is a WireGuard tunnel authorized by the ACL —
    the identity that's allowed is the *key*, never the address.

**Do it:**

```bash
docker compose exec node sh -c 'apk add -q curl 2>/dev/null; curl -sf http://target-service/'
```

> **▸ On track if:** you get the nginx page back — `Corp — Internal Service`, `Status: OK`, and the
> line *"only reachable from devices registered in the headscale mesh with the `tag:corp-managed`
> tag."* Capture this exact command + output — it's half the proof.

### Step 3 — Prove an off-mesh device is denied (the deliverable)

??? note "Concept (30 sec)"
    Flight-card #5. The honest proof of device-bound access is the **deny**, and you prove it two ways
    that *actually hold* in this env: (a) from your **host** there is no route — the target has no
    published port; (b) a container that is **not attached to the mesh network** cannot resolve or
    reach `target-service`. No mesh membership = no access, exactly as a default-deny ACL intends.

**Do it — run an ad-hoc container that is *not* on the mesh network:**

```bash
# no --network flag → this container is NOT a mesh member
docker run --rm curlimages/curl:8.9.1 curl -s --max-time 5 http://target-service/ ; echo "exit=$?"
```

> **▸ On track if:** it fails — a resolve error / `Could not resolve host` / timeout, and a **non-zero
> exit** (`exit=6` or `exit=28`). Contrast with the enrolled `curl` in Step 2 that returned the page.
> **This enrolled-succeeds / off-mesh-fails pair is the centerpiece artifact** — access bound to mesh
> membership, not to a credential or an address.

!!! warning "Don't fool yourself"
    If you instead attach the ad-hoc container *to* the mesh network (`docker network ls | grep
    ztna-net` to find its name, then `docker run --network <name> …`), it **will** reach the target —
    because this lab simulates the data plane with shared Docker networking, not live WireGuard ACL
    enforcement. That's the seam to name in your writeup: the *policy* that makes membership
    conditional on a **tag** lives in `headscale-acl.yaml` (Step 4); a real tailscale client enforces
    it, the stand-in node does not.

### Step 4 — Read the ACL as a Zero-Trust policy

??? note "Concept (30 sec)"
    Flight-card #4. Open `data/headscale-acl.yaml`. It's HuJSON-style: two `accept` stanzas
    (`tag:corp-managed → tag:target:80/443`, and the return path) and **no catch-all `allow *`** — so
    everything unnamed is refused. That final "no catch-all" comment *is* the default-deny.

**Do it:** in `data/headscale-acl.yaml`, identify (a) the tag required to reach `tag:target`, (b) what
happens to a device that registers but is *not* tagged `corp-managed`, and (c) how you'd add a
**second tier** so contractor devices reach only a `tag:contractor-allowed` subset. Draft that extra
stanza into your deliverable.

> **▸ On track if:** you can point to the exact line that grants `tag:corp-managed → tag:target`, state
> that an untagged/unenrolled device gets **nothing** (no matching accept rule), and your contractor
> stanza adds a *narrow* `tag:contractor-allowed → tag:contractor-allowed`-style grant **without**
> introducing an `allow *`. If your new stanza widens reach for anyone unnamed, you wrote an implicit
> default-allow — the trap.

### Step 5 — Map posture to production controls (honestly: assessed, not demonstrated)

??? note "Concept (30 sec)"
    Flight-card #6. `data/device-posture-policy.json` is the checks a production deployment (Cloudflare
    Access + CrowdStrike) enforces: CrowdStrike ZTA score ≥70, minimum OS build, disk encryption
    enabled, firewall/screen-lock warnings — plus a weaker contractor-BYOD tier and a
    `default_posture: deny_all`. None of it runs here; you *reason* about it.

**Do it:** for each `required_check`, name the device-trust gap it closes and map it to the **LastPass**
failure it would have caught (the unpatched Plex host → `os_version`; no EDR on a personal box →
`edr_enrolled`). Write the mapping table and **label the section "assessed from config."**

> **▸ On track if:** every check ties to a concrete gap, at least one row names the LastPass home
> machine explicitly, and the section is labelled *assessed from config* — you are not claiming the lab
> ran a CrowdStrike query.

### Step 6 — Feel the FIDO2 ceremony (browser)

**Do it:** at [WebAuthn.io](https://webauthn.io/), register a passkey with your built-in authenticator
(Touch ID / Windows Hello / a software authenticator), then authenticate. Write one paragraph: what
happens at **registration** (keypair created, private key stays on device, public key stored by the
relying party), what happens at **authentication** (challenge signed by the private key), and why the
key never leaves the device boundary. Tie it to **NIST 800-207 Tenet 3** and the module's split —
WireGuard proves the device, FIDO2 proves the user on it.

> **▸ On track if:** your paragraph names the challenge-response and the never-exported private key, and
> connects both halves (device + user) to Tenet 3 — not just "I logged in with Touch ID."

---

## Prove the control (your finish line)

Assemble `device-trust-analysis.md` and show the **one contrast that proves device-bound access**:

> The **enrolled `curl` returns the `Corp — Internal Service` page**, and the **off-mesh `curl` fails
> with a non-zero exit** — same target, same command, different device membership. Paste both, with the
> exact commands.

If your off-mesh container *did* reach the target, you either attached it to the mesh network or the
boundary has a hole — resolve that before you call the lab done. That contrast, plus a default-deny ACL
you can read line-by-line, is what makes the analysis credible.

---

## Recall check — close the doc, answer from memory (3 min)

1. Which question did LastPass's access model never ask, and which ATT&CK technique describes the
   attacker's move?
2. Why is an off-mesh container denied here, and why is that a *stand-in* for — not identical to — a
   tag-level WireGuard ACL deny?
3. Name three checks in the posture policy and the device-trust gap each closes. Which one would have
   caught the unpatched Plex host?

Missed one? Re-run the step that built it, or pull the [module's two halves](README.md#the-two-halves-of-device-trust) — then re-answer.

---

## Deliverables

- **`device-trust-analysis.md`** containing:
  - **The device-bound access proof** — enrolled-reaches vs. off-mesh-denied, with exact commands and
    output (the centerpiece artifact).
  - The extended ACL stanza for the contractor tier (no implicit default-allow).
  - The posture-check → device-trust-gap mapping table, labelled *assessed from config*, tying at least
    one check to LastPass-2022.
  - The FIDO2 paragraph.

*Lab artifacts — WireGuard keys, the headscale DB volume — stay out of commits.*

## Automate & own it

**Required.** Write a Bash or Python script (`posture-check.sh` / `posture-check.py`) that runs a device
posture check **locally**: given a set of checks (OS/patch level via `uname -r`, disk-encryption status,
an EDR/agent process running), it returns PASS/FAIL per check and an overall verdict. Have a model draft
it, then **review every check** — a posture check that always returns PASS because its detection logic
is broken is *worse* than no check at all: it manufactures false confidence, the LastPass home machine
"passing." Run it on your own machine and confirm the output reflects reality before committing. (AI
drafts; you prove each check is real and you own it.)

## Definition of done (`device-trust` ✅)

- [ ] `make up` / `make demo` run cleanly; you can explain why `headscale nodes list` is empty (the node
  is a data-plane stand-in) without it being a failure.
- [ ] Both sides of device-bound access are captured: enrolled node returns the `Corp — Internal
  Service` page; an off-mesh container fails with a non-zero exit — exact commands + output for each.
- [ ] The ACL is confirmed **default-deny** (no catch-all `allow *`), and your contractor-tier stanza is
  written, narrow, and free of any implicit default-allow.
- [ ] The posture-check → device-trust-gap table is written and labelled *assessed from config*, with at
  least one row tied to the LastPass Plex/EDR failure.
- [ ] The FIDO2 paragraph ties both halves to NIST 800-207 Tenet 3.
- [ ] `device-trust-analysis.md` + `posture-check.sh` are committed; you can explain all six flight-card
  facts cold.

## Connects forward

- **Module 04 — ZTNA Architectures (ADR)** weighs device-mesh vs. identity-aware-proxy patterns —
  headscale is the "network mesh" option in that decision.
- **Module 05 — SASE** uses Cloudflare's device-posture integration (CrowdStrike ZTA score, OS version)
  as a live gate on application access — the production version of this lab's
  `device-posture-policy.json`, with the posture half actually enforced.
- **Module 06 — Identity-Aware Access** combines device trust with identity at the proxy.

## Marketable proof

> "I can deploy a self-hosted WireGuard mesh with headscale, enforce **device-bound** access via a
> default-deny ACL — proven by denying an off-mesh device — and map device-posture requirements to the
> Tailscale and Cloudflare Access control models, naming honestly what a self-hosted lab demonstrates
> versus assesses: the skills of a ZT infrastructure engineer or network security architect."

## Stretch

- Add a `tag:contractor-allowed` stanza to the ACL, then **verify both paths**: reason (or, with a real
  tailscale client, prove) that a contractor device reaches only the contractor subset and is denied
  `tag:corp-managed` and the financial-system tags — the segmentation, not just the happy path.
- Extend `posture-check.sh` to query the headscale API (`GET /api/v1/node` on `:8088`) for registered
  nodes and flag any whose last-seen timestamp is older than 24 hours — a stale node is a red flag.
