# Lab 03 — Device Trust & Posture: headscale + WireGuard

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You stand up a self-hosted device-identity mesh (headscale +
WireGuard), enroll a device into it, and **prove access is bound to that device** — an enrolled node
reaches the protected service, an unenrolled one is denied. The deliverable is the *running, reviewed
system plus the proof of device-bound access*, not a writeup. No grader; you verify your own work
against the observable success criteria below.

## Setup

This is a **reference lab** with a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/03-device-trust-posture
make up        # start headscale (control server) + the protected target service
make demo      # register a node, list it, and verify device-bound access control
make down      # stop when done
```

The environment starts `headscale` (the coordination/control server on 8080), `target-service` (an
nginx container serving a status page — the protected resource), and `node` (a container that acts as
an enrolled device in the mesh).

> Everything runs locally inside Docker networking. No external services are contacted.

## Scenario

A remote-access model that extends trust to **any authenticated user regardless of device** is the
LastPass-2022 failure waiting to happen: a contractor's BYOD laptop — no EDR, unknown patch level, no
disk encryption — gets the same reach as a fully managed corporate machine, and one keylogged
credential on the unmanaged box becomes a launch point into everything behind the VPN. You'll stand up
headscale as the ZT-aligned alternative where **access is bound to a known device, not just a
credential**, prove that only an enrolled device can reach the protected service, and map a structured
device-posture policy to the controls a production deployment (Cloudflare Access + an EDR like
CrowdStrike) would enforce — honestly labelling that posture half as *assessed from config*, since it
can't be self-hosted for free.

> **Authorization note:** this lab attacks/probes only the containers it ships. Only ever run access
> probes against systems you own or have explicit written permission to test.

## Do

Build the mesh, operate it, then prove access is device-bound — the unenrolled device must be denied.

**Build & operate the device-identity mesh**
1. [ ] `make up` then `make demo`. Watch the `node` container generate a WireGuard keypair and
   register with headscale, then confirm it appears in `headscale nodes list`. Now inspect the ACL
   (`data/headscale-acl.yaml`): which tag is required to reach `tag:target`, and — crucially — what is
   the default disposition for a device that is *not* enrolled or *not* tagged? (Goal: confirm the
   policy is **default-deny**, not default-allow.)

2. [ ] **Prove access from the enrolled device.** Shell into the registered node and reach the target:
   ```bash
   docker compose exec node curl -s http://target-service/
   ```
   You should see the nginx status page. This device holds a WireGuard keypair registered with
   headscale — its *identity* is what the ACL allows, not its IP.

**Prove access is device-bound (the deliverable)**
3. [ ] **Prove an unenrolled device is denied.** Start an ad-hoc container with **no** registered
   keypair and try to reach the service:
   ```bash
   docker run --rm --network ztna-03_ztna-net curlimages/curl:8.9.1 \
     curl -s --max-time 5 http://target-service/
   ```
   This must time out or be refused — the service is reachable only via the mesh ACL, and an
   unenrolled device has no identity the ACL trusts. **Capture the exact command and output for both
   the enrolled and unenrolled case: this contrast is the artifact** — access bound to a known device,
   not a credential.

**Reason about and extend the ACL (the ZT judgment)**
4. [ ] **Read the ACL as a Zero-Trust policy.** In `data/headscale-acl.yaml`, identify (a) the tag
   required for `tag:target`, (b) what happens to a device that is registered but *not* tagged
   `corp-managed`, and (c) how you'd add a second tier so contractor devices reach only a
   `tag:contractor-allowed` subset. Write that additional stanza into your deliverable. Watch for the
   trap: a stanza that accidentally introduces an **implicit default-allow** is the opposite of ZT,
   however valid it looks.

**Map posture to production controls (honestly: assessed, not demonstrated)**
5. [ ] **Read the posture policy.** Open `data/device-posture-policy.json` — the checks a production
   deployment (Cloudflare Access + CrowdStrike) would enforce (patch level, EDR running, disk
   encryption). For each check, name the device-trust gap it closes, and map it to the LastPass-2022
   failure it would have caught (the unpatched home machine, the disabled/absent EDR). Write the
   mapping table. **Label this section "assessed from config":** the lab proves device *identity*; this
   posture half is what an EDR/MDM stack would *enforce* — you are reasoning about it, not running it.

**FIDO2 / passkeys (browser exercise)**
6. [ ] Go to [WebAuthn.io](https://webauthn.io/), register a passkey with your built-in authenticator
   (Touch ID / Windows Hello / a software authenticator), then authenticate with it. In your
   deliverable, write a short paragraph: what cryptographic operation happens at registration, what
   happens at authentication, and why the private key never leaves the device boundary. Relate it to
   NIST 800-207 Tenet 3 — and to the module's split: WireGuard proves the device, FIDO2 proves the
   user on it.

## Success criteria — you're done when

- [ ] `make demo` runs cleanly and the enrolled node appears in `headscale nodes list`.
- [ ] You have proven **both** sides of device-bound access: an enrolled node reaches `target-service`
      and an unenrolled container is denied — with exact commands and output captured for each.
- [ ] The ACL is confirmed **default-deny**, and your contractor-tier extension stanza is written and
      syntactically correct (no implicit default-allow).
- [ ] The posture-check → device-trust-gap mapping table is written and explicitly labelled *assessed
      from config*, tying at least one check to the LastPass-2022 failure.
- [ ] The FIDO2 paragraph is in the deliverable.

## Deliverables

`device-trust-analysis.md` containing:
- **The device-bound access proof** — enrolled-reaches vs. unenrolled-denied, with exact commands and
  output (this is the centerpiece artifact).
- The extended ACL stanza for the contractor tier.
- The posture-check → device-trust-gap mapping table, labelled *assessed from config*.
- The FIDO2 paragraph.

Lab *artifacts* (WireGuard keys, the headscale DB) stay out of commits.

## Automate & own it

**Required.** Write a Bash or Python script (`posture-check.sh` / `posture-check.py`) that runs a
device posture check **locally**: given a set of checks (OS/patch level via `uname -r` or
`systeminfo`, disk-encryption status, an EDR process running), it returns PASS/FAIL per check and an
overall verdict. Have a model draft it, then **review every check** — a posture check that always
returns PASS because its detection logic is broken is *worse* than no check at all (it manufactures
false confidence, the LastPass home machine "passing"). Run it on your own machine and confirm the
output reflects reality before committing. (AI drafts; you prove each check is real and you own it.)

## AI acceleration

Models generate headscale/Tailscale ACL HuJSON and posture JSON accurately — use one to draft the
contractor-tier stanza. Then refuse to trust it: the test is **can you construct a `curl` from an
untagged/unenrolled container that succeeds?** If yes, the ACL has an implicit default-allow and the
model's valid-looking output was wrong. Manually verify against the ACL spec that a `tag:contractor`
device cannot reach `tag:corp-only`. You direct it; you own the deny.

## Connects forward

- **Module 04 (ZTNA Architectures, ADR)** weighs device-mesh vs. proxy patterns — headscale is the
  "network mesh" option in that decision.
- **Module 05 (SASE)** uses Cloudflare's device-posture integration (CrowdStrike ZTA score, OS
  version) as a gate on application access — the production version of this lab's
  `device-posture-policy.json`, with the posture half actually enforced.
- **Module 06 (Identity-Aware Access)** combines device trust with identity at the proxy.

## Marketable proof

> "I can deploy a self-hosted WireGuard mesh with headscale, enforce **device-bound** access via
> default-deny ACLs — proven by denying an unenrolled device — and map device-posture requirements to
> the Tailscale and Cloudflare Access control models: the skills of a ZT infrastructure engineer or
> network security architect."

## Stretch

- Register a second node tagged `contractor`, write an ACL that lets it reach `tag:contractor-allowed`
  but blocks `tag:corp-only`, and verify **both** paths with `curl` from inside the respective
  containers — proving the segmentation, not just the happy path.
- Extend `posture-check.sh` to query the headscale API (`GET /api/v1/node`) for registered nodes,
  flag any whose last-seen timestamp is older than 24 hours (a stale node is a red flag), and report
  the overdue ones.
