# Lab 13 — Privileged Access with Teleport

> **Hands-on lab.** Environment: `plaintext-labs/ztna/13-privileged-access`.
> Objective: **mint yourself a short-lived, identity-bound certificate, SSH to a privileged target
> THROUGH a proxy that records the session, and prove the boundary two ways: an unauthorized role is
> denied, and a direct connection that skips the proxy is refused.** Target: **~90 min**, one finish
> line. This is a **reference lab — a one-command Docker environment** (Teleport auth+proxy, a target
> node, an operator client).

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A privileged session is a certificate you PROVE, not a key you HOLD.** | A held key can be stolen and reused forever (Uber's hardcoded PAM admin credential); a minted, short-lived cert can't. |
| 2 | **RBAC binds three things: `logins` + `node_labels` + `options` — all three must match.** | A valid certificate with the wrong role is still denied. Identity ≠ authorization. |
| 3 | **The proxy is the only path in — the node dials OUT to it.** | Nothing listens on the node for a "skip the proxy" attempt to reach. |
| 4 | **Short TTL (minutes) + no standing secret.** | A leaked certificate expires on its own; a leaked static key doesn't. |
| 5 | **TTL and RBAC scope are independent blast-radius controls.** | A wildcarded role is still a skeleton key — just a temporary one. Both must be tight. |
| 6 | **The session recording is the audit artifact.** | Every privileged session is a replayable tape — "who did what" is a query, not a hope. |

*(The claim you're proving: **a short-lived, role-scoped certificate — not a standing key and not network
position — is what grants privileged access.**)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) and the
> [RBAC-is-a-chain-of-gates](README.md#rbac-is-a-chain-of-gates-not-a-network-path) and
> [Uber case study](README.md#the-case-standing-credentials-no-session-boundary-total-blast-radius)
> sections.

---

## Warm-up — answer before you bring the lab up (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Two admins share one SSH private key to a bastion. What does possessing that key structurally prove
   about who is actually typing on the other end? What does a per-identity certificate prove instead?
2. A role grants `node_labels: '*': '*'`. Even if every certificate that role issues expires in 5
   minutes, what is still wrong with it?

---

## Setup

The environment lives in the companion `plaintext-labs` repo — one locally-built image runs Teleport's
auth+proxy service, a target node, and an operator client. No cloud account required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/13-privileged-access
make up          # build + start auth/proxy + node, bootstrap roles/users/join-token
make login       # mint alice a short-lived cert and log in
make ssh         # alice SSHes to app-prod-01 THROUGH THE PROXY — recorded
make play        # list recordings, replay the one you just made
make deny-role   # prove a user WITHOUT the right role is denied (mallory)
make deny-expired  # prove an EXPIRED certificate is denied
make deny-bypass   # prove a direct connection, skipping the proxy, is refused
make tighten     # apply the least-privilege version of alice's role (Step 5)
make demo        # the full walkthrough (allow + record, then both denials)
make shell       # drop into the client container (tsh CLI available)
make down        # stop when done
```

> **▸ On track if:** `make up` ends with `Lab ready. Try: make login | make ssh | make demo`. The
> target node (`app-prod-01`) publishes **no ports** — it joins the cluster by dialing *out* to the
> proxy, and that absence of a listener is itself the security property Step 4 proves.

> **Authorization note.** Everything runs locally against containers you own — no external targets, so
> no authorization is needed here. (The rule still binds anywhere you point a tool at a system you
> don't own: only test what you own or have explicit written permission to test.)

---

## Build it — read a little, do a little

### Step 1 — Bring it up and read what got created

**Concept (30 sec):** Flight-card #2. Two RBAC roles exist before you touch anything: `privileged-ops`
(alice's role — **deliberately over-broad**: `root` login, every node) and `help-desk-staging`
(mallory's role — a *real*, correctly-scoped role for a different environment, not a placeholder).

**Do it:** `make up`, then read what the bootstrap step created:
```bash
docker compose exec teleport-auth tctl get roles --format=text
docker compose exec teleport-auth tctl get users --format=text
```
Also read `data/role-privileged-ops.yaml` — note `node_labels: "*": "*"` and `logins: [root, ubuntu]`.
That wildcard is the thing Step 5 fixes.

> **▸ On track if:** you see both roles and both users. `privileged-ops` shows the wildcard
> `node_labels`; `help-desk-staging` shows `node_labels: {env: [staging]}` — a real scope, just not
> *this* node's.

### Step 2 — Mint yourself a short-lived certificate and log in

**Concept (30 sec):** Flight-card #1 + #4. `tctl auth sign` is the administrator's offline equivalent of
`tsh login` — it signs a certificate straight from the cluster CA for an existing user, scoped to that
user's roles, with an explicit TTL you set. No password, no browser. Read `workload/mint-cert.sh`.

**Do it:** `make login`, then read the identity you just adopted:
```bash
docker compose exec client bash /opt/teleport/workload/operate.sh alice status
```
Note the **TTL** (valid for ~15 minutes) and the **role** baked into the certificate.

> **▸ On track if:** `tsh status` shows `Logged in as: alice`, `Roles: privileged-ops`, and a `Valid
> until` timestamp roughly 15 minutes out. Nothing you hold is good for longer than that on purpose.

### Step 3 — SSH through the proxy; watch the session get recorded

**Concept (30 sec):** Flight-card #3 + #6. `tsh ssh` never talks to the node directly — it connects to
the **proxy**, presents your certificate, and the proxy relays the session over the reverse tunnel the
node opened outbound. Every byte is captured as it happens.

**Do it:** `make ssh`, then `make play`.

> **▸ On track if:** the SSH output shows `ubuntu`, the hostname `app-prod-01`, and `privileged session
> OK`. `make play` lists at least one recording and replays it — you should see the same commands you
> just ran, verbatim. *That replay is the audit artifact* — not a log line claiming a session happened,
> the session itself.

### Step 4 — Prove the boundary, three ways

**Concept (30 sec):** The core claim, from three angles: wrong role, expired cert, and skip-the-proxy
entirely.

**Do it:**
```bash
make deny-role      # mallory's role doesn't cover this node's labels
make deny-expired    # a 30-second cert, used 35 seconds later
make deny-bypass     # nc straight at app-prod-01:3022, bypassing the proxy
```

> **▸ On track if:** `deny-role` shows an access-denied error for mallory (same certificate mechanism,
> wrong role). `deny-expired` shows a certificate-expired error. `deny-bypass` shows **connection
> refused** — not a timeout, not a firewall drop, but *nothing listening* on the other end, because the
> node never opened an inbound port to begin with. If any of the three unexpectedly succeeds, that's a
> bug to chase before moving on — re-check the role YAML or `conf/node.yaml`.

### Step 5 — Tighten `privileged-ops` to least privilege (the judgment step)

**Concept (30 sec):** Flight-card #5. `privileged-ops` currently grants `root` and every node in the
fleet. This lab only *has* one node, and the job only needs one login. A short TTL doesn't fix an
over-broad role — it just bounds how long the over-broad grant is dangerous for.

**Do it:** read `data/role-privileged-ops-tightened.yaml` (logins narrowed to `ubuntu`, `node_labels`
narrowed to `env: production`), then apply it:
```bash
make tighten
make ssh      # re-run — alice should still succeed with the narrower role
```

> **▸ On track if:** `make ssh` still succeeds after tightening — proving least privilege didn't break
> the legitimate path — and you can explain out loud why `root` + wildcard labels was a real risk even
> at a 15-minute TTL (hint: it's not about *how long*, it's about *how much*, per flight-card #5).

---

## Prove the control (your finish line)

Run the one assertion that proves the whole control at once — allowed, unauthorized-denied, and
bypass-refused:

```bash
make check
```

**The proof:** `check-access.sh` asserts that **alice** (privileged-ops) reaches `app-prod-01` as
`ubuntu`, that **mallory** (help-desk-staging — a real role, wrong environment) is **denied**, and that
a **direct connection to `app-prod-01:3022`, skipping the proxy, is refused**.

> **▸ On track if:** you see `PASS alice (privileged-ops) -> ubuntu@app-prod-01 succeeded`, `PASS
> mallory (help-desk-staging, env=staging) denied access to app-prod-01 (env=production)`, `PASS direct
> connection to app-prod-01:3022 refused`, and a final `3 passed, 0 failed`. The two denials are the
> proof: identity alone isn't enough, and network reachability to the target doesn't exist at all.

---

## Recall check — close the docs, answer from memory (3 min)

1. A certificate proves *who* is connecting. What does it **not** prove on its own, and which part of a
   Teleport role closes that gap?
2. Name the two independent blast-radius controls this lab builds, and what each one bounds — *how
   long* vs. *how much*.
3. Why is "the node has no listening SSH port" a structurally stronger guarantee than "the node's SSH
   port is firewalled off"?

Missed one? Re-run the step that built it, or pull the [core idea](README.md#the-core-idea) — then
re-answer.

---

## Deliverables

- **`findings.md`** — the privileged-access write-up: the two roles (as found, before Step 5), the
  certificate TTL and identity from `tsh status`, the recorded session (what the replay showed), all
  three denials from Step 4, and the Step 5 tightening rationale (why `root` + wildcard labels was a
  risk independent of TTL). A portfolio artifact: it shows you can replace a standing-key bastion with
  certificate-based, role-scoped, recorded privileged access — and prove the deny path.

*Never commit certificates, keys, or the join token — they're in `.gitignore`.*

## Automate & own it

**Required.** A recording that exists but is never checked is a log nobody reads. Extend the regression
test: write `verify-recording.sh` that, after an `alice` SSH session, plays back the most recent
recording in machine-readable form and **asserts the specific command you ran appears in it** —
```bash
docker compose exec client bash -c \
  'TELEPORT_HOME=/root/.tsh-alice tsh play --format=json <session-id>'
```
— parse the event stream (`jq` is already in the image) for the command text, and fail loudly if it's
missing. Have a model draft the `jq` filter over the JSON event stream; **you verify** it actually finds
the command in a real recording and actually fails on a recording that doesn't contain it — a check that
always passes is worse than no check. Commit it as `verify-recording.sh`.

> **Seam, labeled honestly:** the exact JSON field layout of `tsh recordings ls --format=json` and
> `tsh play --format=json` has shifted across Teleport releases, and this lab pins one specific version
> (18.10.0) rather than chasing every schema. `workload/operate.sh`'s `play-latest` action already
> defends against a couple of likely field names; if your Teleport version's schema differs, inspect one
> real event stream with `jq .` first and adjust the filter — that's a five-minute fix, not a redesign.

## Definition of done (`privileged-access` ✅)

- [ ] `make up` bootstraps two roles and two users; `tctl get roles` shows `privileged-ops` (wildcarded) and `help-desk-staging` (scoped to `staging`).
- [ ] `make login` + `tsh status` shows `alice`, role `privileged-ops`, and a TTL of roughly 15 minutes.
- [ ] `make ssh` reaches `app-prod-01` as `ubuntu` through the proxy; `make play` replays that exact session.
- [ ] `make deny-role`, `make deny-expired`, and `make deny-bypass` each show a distinct refusal.
- [ ] `make tighten` applies the least-privilege role, and `make ssh` still succeeds afterward.
- [ ] `make check` ends `3 passed, 0 failed`.
- [ ] `findings.md` + `verify-recording.sh` are committed; you can explain all six flight-card facts cold.

## Connects forward

This is the human-operator counterpart to Module 12: a Teleport certificate is to a privileged session
what a SPIFFE SVID is to a workload — short-lived, identity-bound, fetched or signed just before use,
useless once it expires. Module 02 gave you the identity (the OIDC token that proves *who* alice is);
this module is what happens once that identity needs to touch infrastructure, not just an app. And the
session recording you played back in Step 3 is exactly the kind of artifact the **capstone** expects as
evidence — an audit trail that proves what happened, not a claim that it did.

## Marketable proof

> "I replace standing SSH keys and a shared bastion with short-lived, identity-bound certificates and
> per-session RBAC — so every privileged session to production infrastructure is authorized by role, not
> by who holds a key, and is recorded end-to-end as its own audit trail."

## Stretch

- **Just-in-time elevation.** Teleport Access Requests let a user request a role (and TTL) on demand
  instead of holding `privileged-ops` standing: try `tsh request create --roles=privileged-ops
  --reason="investigating ledger latency"` and approve it with `tctl request ls` / `tctl request
  approve <id>`. The core request/approve loop is a Community Edition feature; note honestly that some
  *approval-routing* integrations (Slack, PagerDuty) are Enterprise-only — this stretch only needs the
  CLI loop.
- **A second, correctly-reachable node.** Add a `teleport-node-staging` service labeled `env: staging`
  and re-run mallory's SSH attempt against *it* — proving `help-desk-staging` isn't a "deny everything"
  role, it's precisely scoped, and it works exactly where it should.
- **Shorten the TTL under a live session.** Mint a 1-minute certificate, start an interactive `tsh ssh`
  session, and watch what happens to the connection as the certificate's `Valid until` passes — confirm
  whether the existing session survives (session-bound) or a *new* connection attempt is what actually
  gets refused, and be able to explain the difference.
