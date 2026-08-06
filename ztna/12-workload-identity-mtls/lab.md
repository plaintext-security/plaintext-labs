# Lab 12 — Workload Identity & mTLS with SPIFFE/SPIRE

> **Hands-on lab.** Environment: `plaintext-labs/ztna/12-workload-identity-mtls`.
> Objective: **issue each workload a short-lived SPIFFE identity, prove service-to-service mTLS keyed
> on it, and prove an unregistered workload gets nothing.** Target: **~90 min**, one finish line. This
> is a **reference lab — a one-command Docker environment** (SPIRE server + agent + two workloads).

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Identity is a credential you PROVE (an SVID), not a secret you HOLD.** | A held key can be stolen and reused (Capital One); a fetched, short-lived SVID can't. |
| 2 | **Two-layer attestation:** the agent proves the *node*, then attests each *workload* by selectors it can't forge. | This is how a brand-new workload gets its first credential without being pre-trusted. |
| 3 | **mTLS keyed on identity:** both ends present an SVID and validate the peer's **SPIFFE ID**. | `Verify return code: 0` means *both* sides were authenticated by identity, not IP. |
| 4 | **Short TTL + auto-rotation** (300s here). | Nothing long-lived sits in the image; a leaked SVID expires in minutes. |
| 5 | **The selector is the whole security decision.** | A loose selector (a shared UID, a label anything can set) = a wildcard IAM grant. |
| 6 | **Authentication, not authorization.** | SPIFFE proves *who* is calling; a policy engine (OPA module) decides *whether* — identity here, decision there. |

*(The claim you're proving: **identity, not network position, grants access** — `rogue` sits on the
same network as `client` and still gets nothing.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) and the [two-layer attestation](README.md#how-a-workload-earns-its-identity-two-layer-attestation)
> and [handshake](README.md#the-handshake-mutual-tls-keyed-on-the-svid) sections.

---

## Warm-up — answer before you bring the lab up (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Two services sit on the **same** network segment. A label-based allow rule lets them connect. What
   does that rule *not* force the caller to do that workload identity does?
2. A container just started and holds no credential yet. How can SPIRE hand it its first SVID without
   you having already trusted it — what is the agent *inspecting* to decide?

---

## Setup

The environment lives in the companion `plaintext-labs` repo — one locally-built image runs a SPIRE
server, a one-shot bootstrap, an agent, and two workloads. No cloud account required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/12-workload-identity-mtls
make up        # build + start SPIRE (server, agent), bootstrap entries, start the workloads
make mtls      # client fetches its SVID and makes a mutual-TLS call to the backend
make deny      # prove an unregistered workload is refused an identity
make check     # assert: registered workloads get the right SVID, rogue gets none
make demo      # the full walkthrough (mTLS success, then the deny)
make shell     # drop into the client workload (spire-agent CLI + openssl)
make down      # stop when done
```

> **▸ On track if:** `make up` finishes with `Lab ready. Try: make mtls | make deny | make demo`. The
> agent uses the **Docker workload attestor**, so it needs the host's Docker socket and PID namespace
> (already wired in `docker-compose.yml`) to map a calling workload back to its container labels.

> **Authorization note.** Everything runs locally against containers you own — no external targets, so
> no authorization is needed here. (The rule still binds anywhere you point a tool at a system you
> don't own: only test what you own or have explicit written permission to test.)

---

## Build it — read a little, do a little

### Step 1 — Bring it up and read what got registered

**Concept (30 sec):** Flight-card #2. A **registration entry** maps a *selector the agent can observe*
(`docker:label:com.corp.svc:<name>`) to a *SPIFFE ID* (`spiffe://corp.local/<name>`). Two workloads are
registered on purpose; `rogue` is deliberately left out.

**Do it:** `make up`, then read the entries the server issued:
```bash
docker compose exec spire-server spire-server entry show -socketPath /tmp/spire-server/private/api.sock
```
Where are these created? Read `data/setup.sh` — note it registers `backend` and `client` and
*nothing* for `rogue`.

> **▸ On track if:** you see **two** entries, each pairing a selector `docker:label:com.corp.svc:backend`
> / `…:client` to `spiffe://corp.local/backend` / `…/client`. No entry mentions `rogue`.

### Step 2 — Watch a workload fetch its own identity

**Concept (30 sec):** Flight-card #1 + #4. The workload holds no baked-in key — it *fetches* its SVID
from the Workload API at runtime, with a short TTL, and the agent re-issues it before it expires.

**Do it:** `make shell` (drops you into `client`), then:
```bash
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
```
Read the **SPIFFE ID**, the SVID's **TTL** (~300s / 5 min), and note no secret was ever handed to the
workload. Re-run after a few minutes — the SVID has rotated.

> **▸ On track if:** the output shows `SPIFFE ID: spiffe://corp.local/client` and a TTL on the order of
> 300 seconds. A second fetch minutes later shows a fresh certificate — nothing long-lived to steal.

### Step 3 — Prove identity with mutual TLS

**Concept (30 sec):** Flight-card #3. In an mTLS handshake *both* ends present an SVID and validate the
peer against the same trust bundle — the trust decision is the peer's **SPIFFE ID**, not its IP.

**Do it:** `make mtls` (or run `/opt/spire/workload/connect.sh` from the client shell). The client
fetches its SVID and connects to the backend on `:8443`. Read `workload/backend.sh` — which
`openssl s_server` flag is what *requires* the client to present a valid cert? (Answer: `-Verify 1`.)

> **▸ On track if:** the output contains `hello from spiffe://corp.local/backend`, `Verify return
> code: 0`, and `✅ mutual TLS succeeded — both ends presented a valid SVID.` Both sides were
> authenticated by identity.

### Step 4 — Prove the boundary: no identity, no access

**Concept (30 sec):** The core claim. `rogue` carries a label (`com.corp.svc=rogue`) that matches **no
registration entry**, so the Workload API refuses it an SVID — even though it's on the *same network*
as `client`.

**Do it:** `make deny`. Watch `rogue` ask the Workload API for an SVID and get refused; with no cert to
present, it cannot complete an mTLS handshake to the backend.

> **▸ On track if:** `rogue`'s fetch returns **no SVID** (a "no identity issued" / refused result), and
> you can articulate: same network as `client`, different outcome — because identity, not position,
> grants access. If `rogue` somehow got an identity, a selector is too loose — recheck `data/setup.sh`.

### Step 5 — Tighten a selector (the judgment step)

**Concept (30 sec):** Flight-card #5. The lab attests on a Docker *label*, which any deployment could
set. In a real environment you pin to something harder to forge.

**Do it:** in your write-up, name a stronger selector (an image **digest**, a Kubernetes **service
account** bound to a namespace) and explain why a loose selector is the workload-identity equivalent of
a wildcard IAM grant. Optionally edit `data/setup.sh` to add an image-based selector to one entry and
re-verify it still issues.

> **▸ On track if:** your write-up answers "could a different workload satisfy this selector?" for the
> label case and proposes a selector where the answer is *no*.

---

## Prove the control (your finish line)

Run the one assertion that proves the whole control at once — identified-allowed vs. unidentified-denied:

```bash
make check
```

**The proof:** `check_identity.sh` asserts that `backend` receives exactly `spiffe://corp.local/backend`,
`client` receives exactly `spiffe://corp.local/client`, and `rogue` receives **nothing**.

> **▸ On track if:** you see `PASS backend -> spiffe://corp.local/backend`, `PASS client -> …/client`,
> `PASS rogue received no SVID`, and a final `N passed, 0 failed`. That single run is the control: two
> workloads on the same network, and only the ones with a provable identity get in.

---

## Recall check — close the docs, answer from memory (3 min)

1. What does an mTLS `Verify return code: 0` prove that a network-segment allow rule never can?
2. Two layers of attestation — what does the agent prove to the *server*, and what does it then attest
   about each *workload*? Why can't the workload forge the second?
3. SPIFFE proves *which* workload is calling — so what is it **not** doing, and where does that
   decision belong instead?

Missed one? Re-run the step that built it, or pull the [core idea](README.md#the-core-idea) — then
re-answer.

---

## Deliverables

- **`findings.md`** — the workload-identity write-up: the two registration entries, the runtime SVID
  fetch (with TTL), the mTLS proof (both ends verified, `Verify return code: 0`), the
  unregistered-workload deny, and the selector-strength analysis from step 5. A portfolio artifact: it
  shows you can issue provable workload identities, key mTLS on them, and demonstrate the deny.

*Never commit SVIDs, private keys, or the join token — they're in `.gitignore`.*

## Automate & own it

**Required.** Replace the `openssl` plumbing with a real SPIFFE-aware mTLS client: write a small Go
program using [`go-spiffe/v2`](https://github.com/spiffe/go-spiffe) (or Python with `pyspiffe`) that
connects to the backend off the Workload API, **authorizes the peer by SPIFFE ID** (accept only
`spiffe://corp.local/backend`), and fails closed on any other identity. Have a model draft the
`workloadapi` + `tlsconfig` calls; **you verify** it rejects a peer whose SPIFFE ID doesn't match —
authenticating the channel is worthless if you don't check *who* is on the other end. Commit it as
`mtls-client/`.

## Definition of done (`workload-identity` ✅)

- [ ] `make up` issues SVIDs; `spire-server entry show` lists exactly the `backend` and `client` entries (none for `rogue`).
- [ ] A runtime SVID fetch from `client` shows `spiffe://corp.local/client` with a short (~300s) TTL, and re-fetches show rotation.
- [ ] `make mtls` completes with `hello from spiffe://corp.local/backend`, `Verify return code: 0`, and the success line.
- [ ] `make deny` shows the unregistered `rogue` is refused an SVID and cannot connect.
- [ ] `make check` ends `N passed, 0 failed` — identified-allowed and unidentified-denied both proven.
- [ ] `findings.md` + `mtls-client/` are committed; you can explain all six flight-card facts cold.

## Connects forward

This is the service-to-service counterpart to the human-facing modules: a SVID is to a workload what a
short-lived OIDC token is to a user, and what a device key is to a laptop. SPIFFE *authenticates* the
workload; the **OPA module** *authorizes* it — feed the peer's SPIFFE ID into a Rego policy to decide
whether `…/web` may call `…/ledger`. And the SVID-issuance + mTLS-handshake events are exactly the
identity-rich telemetry the detection module hunts against.

## Marketable proof

> "I stand up a SPIFFE/SPIRE trust domain, issue short-lived auto-rotating workload identities, and
> enforce mutual TLS between services keyed on SPIFFE ID — so service-to-service access is granted by
> provable identity, not network position, and an unregistered workload gets nothing."

## Stretch

- Add a third workload (`ledger`) and write a go-spiffe server that authorizes *only*
  `spiffe://corp.local/backend` to call it — then prove `client` is rejected even though it holds a
  valid SVID (authentication succeeds, authorization denies). That's the SPIFFE→OPA handoff in miniature.
- Shorten `default_x509_svid_ttl` (or the entry's `-x509SVIDTTL`) to `1m` and watch the agent rotate
  the SVID under a live mTLS connection; confirm long-lived connections survive rotation while new ones
  get the fresh cert.
- Swap the Docker attestor for the **unix** (UID-based) attestor and construct a workload that
  satisfies that selector without being the intended service — showing concretely why the loose
  selector is the wildcard-grant failure mode.
