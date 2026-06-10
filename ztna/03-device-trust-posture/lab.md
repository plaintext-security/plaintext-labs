# Lab 03 — Device Trust & Posture: headscale + WireGuard

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** with a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/03-device-trust-posture
make up        # start headscale + a target service container
make demo      # register a node, show it in the device list, verify access control
make down      # stop when done
```

The environment starts two containers: `headscale` (the coordination server on port 8080) and
`target-service` (a simple nginx container serving a status page — this is the protected resource).
A third container, `node`, acts as a registered device in the mesh.

> Everything runs locally inside Docker networking. No external services are contacted.

## Scenario

Meridian's current remote access model extends full network trust to any VPN-authenticated user,
regardless of device state. A contractor BYOD laptop — no EDR, unknown patch level, no disk
encryption — gets the same access as a fully managed, CrowdStrike-enrolled corporate laptop. You'll
stand up headscale as a ZT-aligned alternative, demonstrate that only registered devices can reach
the protected service, and map the fictional Meridian device posture policy (in
`data/device-posture-policy.json`) to the controls Tailscale ACLs would enforce in production.

## Do

1. [ ] Run `make up` and then `make demo`. Observe the output: the `node` container registers with
   headscale, and the demo confirms the node appears in `headscale nodes list`. Now inspect the
   headscale ACL configuration — which nodes are allowed to reach the `target-service`? What is
   the default posture for an *unregistered* device (can it reach the service)?

2. [ ] **Verify access from a registered node.** Run a shell in the `node` container and confirm
   it can reach the target service:
   ```bash
   docker compose exec node curl -s http://target-service/
   ```
   You should see the nginx status page. This is a registered device — it has a valid WireGuard
   keypair registered with headscale.

3. [ ] **Verify access is denied from an unregistered container.** Start an ad-hoc container
   without a registered keypair and try to reach the service:
   ```bash
   docker run --rm --network ztna-03_ztna-net curlimages/curl:8.9.1 curl -s --max-time 5 http://target-service/
   ```
   This should time out or be refused. The service is not exposed to the Docker network directly —
   it is only reachable via the mesh ACL. Document what you observe.

4. [ ] **Read the device posture policy.** Open `data/device-posture-policy.json`. It describes
   what a production deployment (Cloudflare Access + CrowdStrike) would check for a Meridian
   device. For each check in the policy, identify which Meridian gap (from Lab 01) it directly
   addresses. Write a mapping table: `posture_check → gap_from_lab01`.

5. [ ] **Reason about the headscale ACL.** Open `data/headscale-acl.yaml` and read the ACL policy.
   Identify: (a) which tag is required to access `tag:target`, (b) what would happen if a device
   was registered but *not* tagged `corp-managed`, and (c) how you would add a second tier for
   contractor devices that can only reach a `tag:contractor-allowed` subset of services. Write the
   additional ACL stanza in your deliverable.

6. [ ] **FIDO2 / passkeys (prose exercise).** Go to [WebAuthn.io](https://webauthn.io/) in your
   browser. Register a passkey (using your browser's built-in authenticator — Touch ID, Windows
   Hello, or a software authenticator). Then authenticate with it. In your deliverable, write a
   paragraph explaining: what cryptographic operation happens during registration, what happens
   during authentication, and why the private key never leaves the device boundary. Relate this to
   NIST 800-207 Tenet 3 (all communication is secured; users and devices are authenticated per-session).

## Success criteria — you're done when

- [ ] `make demo` runs cleanly and shows the registered node in `headscale nodes list`.
- [ ] You have verified that a registered node can reach `target-service` and an unregistered
  container cannot.
- [ ] The posture-to-gap mapping table is written.
- [ ] The ACL extension stanza is written and syntactically correct.
- [ ] The FIDO2 paragraph is in the deliverable.

## Deliverables

`device-trust-analysis.md` containing:
- The registered vs. unregistered access test results (with exact commands and output)
- The posture check → Lab 01 gap mapping table
- The extended ACL stanza for contractor devices
- The FIDO2 paragraph

## Automate & own it

**Required.** Write a Bash or Python script (`posture-check.sh` or `posture-check.py`) that
simulates a device posture check locally: given a set of checks (OS patch level via `uname -r` or
`systeminfo`, disk encryption status, EDR process running), it returns PASS / FAIL per check and an
overall posture verdict. Have a model draft it; **review every check** — a posture check that always
returns PASS because the detection logic is wrong is worse than no check at all. Test it on your
own machine and verify the output reflects reality before committing.

## AI acceleration

Models generate headscale ACL HuJSON and posture policy JSON accurately. Use one to extend the ACL
stanza for the contractor tier — then manually verify it against the headscale ACL spec that a
`tag:contractor` device cannot reach `tag:corp-only` resources. The test is: can you construct a
curl command from an untagged container that succeeds? If yes, the ACL has a hole.

## Connects forward

- Module 04 uses device trust and identity together in the ZTNA architecture patterns — headscale
  represents the "network mesh" pattern in the comparison.
- Module 05 uses Cloudflare's device posture integration (CrowdStrike ZTA score, OS version) as a
  gate on application access — the production version of the `device-posture-policy.json` from this lab.

## Marketable proof

> "I can deploy a WireGuard mesh with headscale, enforce device-level access control via ACL
> policies, and map device posture requirements to both the Tailscale and Cloudflare Access control
> models — the skills for a ZT infrastructure engineer or network security architect."

## Stretch

- Register a second node with a different tag (`contractor`) and write an ACL that allows it to
  reach a different service (`tag:contractor-allowed`) but blocks it from `tag:corp-only`. Verify
  both access paths with curl from inside the respective containers.
- Extend `posture-check.sh` to query the headscale API (`GET /api/v1/node`) for the registered
  nodes, check whether each node's last-seen timestamp is within the last 24 hours (a stale node
  is a red flag), and flag any that are overdue.
