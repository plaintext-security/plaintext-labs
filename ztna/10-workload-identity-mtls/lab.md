# Lab 10 — Workload Identity & mTLS with SPIFFE/SPIRE

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Everything runs
locally in Docker — a SPIRE server, an agent, and two workloads — no cloud account required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/10-workload-identity-mtls
make up        # build + start SPIRE (server, agent), register entries, start the workloads
make mtls      # client fetches its SVID and makes a mutual-TLS call to the backend
make deny      # prove an unregistered workload is refused an identity
make demo      # the full walkthrough (mTLS success, then the deny)
make check     # assert: registered workloads get the right SVID, rogue gets none
make down      # stop when done
```

The lab runs one locally-built image for every service (SPIRE binaries + `openssl`). The agent uses
the **Docker workload attestor**, so it needs the host's Docker socket and PID namespace (already wired
in `docker-compose.yml`) to map a calling workload back to its container labels.

> Everything runs locally against containers you own. No external targets, no authorization needed.
> **First run note:** this environment is new — if `make up`/`make demo` hits a snag on your platform,
> the moving parts are the join-token bootstrap and the Docker attestor (see `data/setup.sh` and the
> `pid: "host"` + `docker.sock` mount on the agent); the fix is almost always there.

## Scenario

Meridian Financial segmented its Kubernetes traffic in Module 07 — frontend can't reach the database
tier. But a pen-test raised the next question: *when the backend calls the ledger, how does the ledger
know it's really the backend and not something that landed in the allowed segment?* Today: a shared API
token in an env var. You'll replace it with **workload identity** — every service gets a short-lived,
auto-rotating SPIFFE identity it proves with mutual TLS, and a service with no issued identity simply
can't connect. This is the application/workload pillar the proxy and segmentation modules don't cover.

## Do

### Part 1: Issue identities to workloads
1. [ ] **Bring it up and read what got registered.** `make up`, then
   `docker compose exec spire-server spire-server entry show -socketPath /tmp/spire-server/private/api.sock`.
   Note the two entries: each maps a **selector** (`docker:label:com.meridian.svc:<name>`) to a
   **SPIFFE ID** (`spiffe://meridian.local/<name>`). The selector is what the agent can observe about a
   workload but the workload can't forge from outside. Where are these created? Read `data/setup.sh`.

2. [ ] **Watch a workload fetch its own identity.** `make shell` (drops you into the `client`), then:
   ```bash
   spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
   ```
   Read the output: the **SPIFFE ID**, the SVID's short **TTL**, and that the cert was issued to *this*
   workload with no secret ever handed to it. Re-run after a few minutes — the SVID rotates. Why is a
   5-minute, auto-rotated cert a stronger posture than a long-lived key in a file?

### Part 2: Prove identity with mutual TLS
3. [ ] **Make the mTLS call.** `make mtls` (or run `/opt/spire/workload/connect.sh` from the client
   shell). The client fetches its SVID and connects to the backend; **both** ends present an SVID and
   validate the peer against the same trust bundle. Confirm `Verify return code: 0` and that the
   backend's identity is `spiffe://meridian.local/backend`. Read `workload/backend.sh` — which
   `openssl s_server` flag is what *requires* the client to present a valid cert?

4. [ ] **Confirm there's no shared secret and no baked-in key.** Inspect the image / the workload
   scripts: the identity is fetched from the Workload API **at runtime** into a tmpfs path, never built
   into the image or stored in an env var. Note in your write-up what an attacker who copies the
   container image gets (answer: no usable credential).

### Part 3: Prove the boundary — no identity, no access
5. [ ] **Run the unregistered workload.** `make deny`. The `rogue` service carries a label
   (`com.meridian.svc=rogue`) that matches **no registration entry**, so the agent's Workload API
   refuses it an SVID. Confirm it gets *no identity*. Then try to make it do mTLS to the backend (it
   has no cert to present) — the handshake cannot complete. This is the core claim: **identity, not
   network position, grants access** — `rogue` is on the same network as `client` and still gets nothing.

6. [ ] **Tighten a selector (the judgment step).** The lab attests on a Docker *label*, which any
   deployment could set. In your write-up, explain what a stronger, harder-to-forge selector would be in
   a real environment (an image **digest**, a Kubernetes **service account** bound to a namespace) and
   why a loose selector is the workload-identity equivalent of a wildcard IAM grant. Optionally edit
   `data/setup.sh` to add an image-based selector to one entry and re-verify it still issues.

## Success criteria — you're done when
- [ ] `make up` issues SVIDs and `make check` shows backend → `…/backend`, client → `…/client`.
- [ ] `make mtls` completes a mutual-TLS call with `Verify return code: 0` and the backend's expected
  SPIFFE ID.
- [ ] `make deny` shows the unregistered `rogue` workload is refused an SVID and cannot connect.
- [ ] `findings.md` records the issued identities, the mTLS proof, the deny result, and your
  selector-hardening reasoning.

## Deliverables
`findings.md` — the workload-identity write-up: the registration entries, the runtime SVID fetch (with
TTL), the mTLS proof (both ends verified), the unregistered-workload deny, and the selector-strength
analysis from step 6. Commit it. **Never commit SVIDs, private keys, or the join token** — they're in
`.gitignore`.

## Automate & own it
**Required.** Replace the `openssl` plumbing with a real SPIFFE-aware mTLS client: write a small Go
program using [`go-spiffe/v2`](https://github.com/spiffe/go-spiffe) (or Python with `pyspiffe`) that
connects to the backend off the Workload API, **authorizes the peer by SPIFFE ID** (accept only
`spiffe://meridian.local/backend`), and fails closed on any other identity. Have a model draft the
`workloadapi` + `tlsconfig` calls; **you verify** it rejects a peer whose SPIFFE ID doesn't match —
authenticating the channel is worthless if you don't check *who* is on the other end. Commit it as
`mtls-client/`.

## AI acceleration
A model writes the SPIRE config, the `spire-server entry create` commands, and the go-spiffe mTLS
boilerplate fluently. Where it can't help is **the selector** — it will pick one that *works*
(`unix:uid:0`, a label anything can set) without seeing that it's forgeable and would hand your
workload's identity to any caller. Review every selector against "could a different workload satisfy
this?", prefer image digests / bound service accounts, and prove the deny with `make deny` /
`make check` before trusting it.

## Connects forward
This is the service-to-service counterpart to the human-facing modules: a SVID is to a workload what
the short-lived OIDC token from **Module 02** is to a user, and what the device key from **Module 03**
is to a laptop. SPIFFE *authenticates* the workload; **Module 08 (OPA)** *authorizes* it — feed the
peer's SPIFFE ID into a Rego policy to decide whether `…/web` may call `…/ledger`. And the SVID
issuance + mTLS handshake events are exactly the identity-rich telemetry **Module 09** detects against.

## Marketable proof
> "I stand up a SPIFFE/SPIRE trust domain, issue short-lived auto-rotating workload identities, and
> enforce mutual TLS between services keyed on SPIFFE ID — so service-to-service access is granted by
> provable identity, not network position, and an unregistered workload gets nothing."

## Stretch
- Add a third workload (`ledger`) and write a go-spiffe server that authorizes *only*
  `spiffe://meridian.local/backend` to call it — then prove `client` is rejected even though it holds a
  valid SVID (authentication succeeds, authorization denies). That's the SPIFFE→OPA handoff in miniature.
- Shorten `default_x509_svid_ttl` to `1m` and watch the agent rotate the SVID under a live mTLS
  connection; confirm long-lived connections survive rotation while new ones get the fresh cert.
- Swap the Docker attestor for the **unix** attestor (UID-based) and discuss why that selector is weaker
  — then construct a workload that satisfies it without being the intended service.
