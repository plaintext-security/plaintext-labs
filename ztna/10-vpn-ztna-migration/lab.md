# Lab 10 — VPN → ZTNA Migration: Cut a Brownfield Estate Over, Cohort by Cohort, With No Outage

*Type 12 · Migration / Brownfield. [← Back to the module concept](README.md)*

**Type 12 · Migration / Brownfield.** You take a running legacy VPN on a flat network — apps that the
whole org reaches today by *being on the network* — and migrate them behind an identity-aware proxy
*incrementally, without an outage*: stand the new path beside the VPN, move apps **one cohort at a time**
behind a DNS/feature-flag cutover, prove each move with a **before/after access test** (still reachable
for authorized users, now via the proxy; the old flat path closing), keep a **rollback per cohort**, and
only at the end **decommission the VPN**. The deliverable is the *migration runbook + per-app cutover
checklist + proof (logs) that no app had an outage + the per-cohort rollback* — not a writeup. No grader;
you verify your own work against the observable success criteria below. (Honor system: the committed
runbook, the proof logs, and the access-test harness are the proof.)

## Setup

> **Lab env to be built at promotion** — this is the ZTNA track's first Type 12 and has no existing
> `plaintext-labs` directory yet. The shape below is the spec (see the **Lab-env spec** at the end of this
> file). It reuses the Pomerium identity-aware proxy from Module 06 as the *new* path and a small
> flat-network stand-in as the *legacy VPN* path, so it stands up entirely in Docker with **zero cloud
> credentials and zero cost**. Until the env exists, every command below is real and runs on a laptop with
> Docker installed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/<NN>-vpn-ztna-migration
make up          # legacy flat network + apps, AND the Pomerium proxy, side-by-side
make demo        # shows an app reachable BOTH ways at start (VPN/flat path AND, once cut over, the proxy)
make cutover COHORT=1   # point cohort 1's traffic at the proxy (DNS/flag flip) + run the before/after test
make rollback COHORT=1  # flip cohort 1 back to the VPN/flat route (the per-cohort rollback)
make decommission       # close the flat network / stop the VPN — only after the last cohort is across
make shell       # drop into a client container to run access tests by hand
make down
```

`make up` stands **two paths up at once**: the **legacy path** is a flat Docker network with a "VPN
client" container that can reach each app directly by internal hostname (`app1.internal`, etc.) — *being
on the network is the only check*; the **new path** is Pomerium (Module 06's proxy) in front of the same
apps, requiring an IdP-issued JWT on every request, with the backends on a network that has no published
port. At start, an app is reachable the old way; the migration is moving each cohort to the new way and
*closing* the old way — that gap is the whole lab.

> **Authorization note:** Only test systems you own or have explicit written permission to test.
> Everything here runs locally in Docker — no external targets, no authorization needed. The
> direct-to-backend "is the old path closed?" probes below are aimed *at your own lab* to prove the
> migration actually removed the flat route, not at any external host. The moment you point this rhythm at
> a real network: only migrate access for infrastructure you own or are authorized to manage, and never
> decommission a VPN before every cohort is provably across with a tested rollback.

## Scenario

An organization has run a VPN for years. Employees, a couple of vendors, and a fleet of CI runners
connect each morning, land on a **flat internal network**, and reach a handful of internal apps directly
— a team wiki, an internal dashboard, and a legacy admin tool — with *no per-request identity check*;
connectivity is the only gate. This is the shape Module 01 autopsied: one compromised VPN credential and
the flat interior is wide open. You've been told to retire the VPN and put every app behind the
identity-aware proxy you built in Module 06 — and the one rule is **no outage**. You cannot pick a
Saturday and flip everything at once: a big-bang cutover changes every access path simultaneously, so when
something breaks you can't tell which change did it, can't roll back one slice, and you're debugging a
company-wide lockout live. So you migrate the strangler-fig way: run both paths, move one cohort at a
time, prove each move didn't break access *and* closed the old route, keep a rollback at every step, and
decommission the VPN only when the last cohort is across.

The rhythm of each cohort: **baseline (reachable via VPN) → cut over (DNS/flag → proxy) → before/after
test (still reachable, now via proxy, AND old flat path closed) → keep the rollback → next cohort.**

## Do

Migrate the brownfield estate behind the proxy, one cohort at a time, proving no outage and that the old
path closes — then decommission the VPN.

**Establish the brownfield baseline (the VPN works; nothing is behind the proxy yet)**
1. [ ] `make up`, then **inventory and baseline**. From the VPN-client container, reach each app the
   *legacy* way (`curl http://app1.internal/`, etc.) and confirm a 200 — *being on the flat network is the
   only check*. Record this baseline per app: **reachable via the VPN/flat path, no identity required.**
   Group the apps into **cohorts** (this lab ships ~3 apps → start with 1 app per cohort) and write the
   cohort order in your runbook **least-risky-first**, with one line of *why* each is safe to move when it
   is (lowest stakes, fewest dependencies, a team you can coordinate with).
2. [ ] **Prove the big-bang trap before you avoid it** (predict, then confirm). In your runbook, write
   what would break if you flipped *all* apps to the proxy at once and turned the VPN off: every access
   path changes simultaneously, so a single failure (an app with a hardcoded internal IP, a service
   account the proxy rejects, a vendor source range you forgot) is indistinguishable from the others, has
   no per-slice rollback, and is debugged as a total outage. **You will not do this** — naming it is the
   point; the cohort rhythm is what prevents it.

**Migrate cohort 1 — cut over, then prove the before/after**
3. [ ] **Record the BEFORE.** For cohort 1's app, capture the baseline access proof: an authorized user
   reaches it *via the VPN/flat route* (200), and note that the request carried **no identity** — the flat
   network let it through. Save this output; it's half the proof.
4. [ ] **Cut the cohort over (and ONLY this cohort).** `make cutover COHORT=1` — flip the cohort's
   cutover switch so its traffic now resolves to the **proxy** (a DNS change pointing `app1.internal` at
   Pomerium, or the feature flag). Confirm cohorts 2..N are **untouched** — they still resolve to the
   VPN/flat route and still serve exactly as before. (This is the strangler-fig guarantee: one slice
   moves; nothing else does.)
5. [ ] **Record the AFTER — and assert all three conditions.** Run the access test against cohort 1's app
   *now*:
   - **(a) Still reachable (NO OUTAGE):** an authorized user (carrying a valid IdP JWT) gets a **200** —
     the app never went down.
   - **(b) Now via the proxy:** the request went *through Pomerium* — the proxy logged an **allow** for
     this request, and the backend echo shows the proxy-injected identity header
     (`X-Pomerium-Jwt-Assertion`), proving identity is now checked on every request. An *unauthenticated*
     request to the same app is now **denied** (non-200), where before it was a free 200.
   - **(c) Old flat path closing:** a **direct** request to the app's backend on the flat network
     (`curl http://app1-backend.internal/` from the VPN client, bypassing the proxy) **no longer
     connects** — the flat route to this app is closed. *If it still connects, the cohort is NOT migrated:
     you've added a ZTNA front door and left the back door open.* Close the flat route for this app, then
     re-test until (c) holds.
6. [ ] **Capture and verify the per-cohort rollback.** Write cohort 1's one-line rollback in the runbook,
   then **run it**: `make rollback COHORT=1` flips the cutover switch back to the VPN/flat route. Confirm
   the app is reachable the old way again within seconds (the VPN was never removed, so backing out is
   cheap), then `make cutover COHORT=1` to restore the migrated state. A rollback you wrote but never ran
   is not a rollback.

**Migrate the remaining cohorts — same loop, prove the rest still works**
7. [ ] Repeat steps 3–6 for each remaining cohort. The strangler-fig constraint at every step: while you
   migrate cohort N, **prove the already-migrated cohorts are still served via the proxy** (their access
   test still passes (a)+(b)+(c)) **and** the not-yet-migrated cohorts are still served via the VPN. You
   shift one cohort at a time; nothing else moves, and you have a tested rollback for each.

**Decommission the VPN — the last, irreversible step**
8. [ ] With **every** cohort migrated and proven (all apps pass (a)+(b)+(c)), and only then, close the
   flat network / stop the VPN: `make decommission`. Re-run the full access test across **all** apps:
   each is still reachable via the proxy (no outage from the decommission), and the flat path is now gone
   everywhere — confirm the VPN-client container can no longer reach *any* backend directly. The
   un-migrated surface is zero. Save this final all-apps proof.

## Success criteria — you're done when
- [ ] You can show the starting state: every app was **reachable via the VPN/flat path with no identity
      check**, and you grouped them into cohorts ordered least-risky-first (with the *why* per cohort).
- [ ] You named the **big-bang trap** in your runbook (all paths change at once; no per-slice rollback;
      debugged as a total outage) — the failure your cohort rhythm avoids.
- [ ] **Every cohort** was cut over and passes the **before/after access test on all three conditions**:
      (a) still reachable for an authorized user — **no outage**; (b) now **via the proxy** (proxy logged
      the allow; injected identity header present; unauth now denied); (c) the **old flat path is closed**
      (direct-to-backend no longer connects).
- [ ] You have a **per-cohort rollback** that you *ran* at least once and proved restores the app on the
      old path in seconds (the VPN was never removed until the end).
- [ ] After the **last** cohort, you decommissioned the VPN and proved **no app had an outage** from the
      decommission **and** the flat path is gone for every backend — the un-migrated surface is zero,
      captured as output.

## Deliverables
Commit to your portfolio repo:
- `migration-runbook.md` — the ordered, strangler-fig runbook: the cohort sequence and *why that order*
  (least-risky-first, dependencies, coordination), and per cohort the cutover mechanism used (the DNS
  record / feature flag), the before/after result, and the named big-bang trap you avoided.
- `cutover-checklist.md` — the **per-app cutover checklist** a teammate could follow without you: for each
  app, the pre-cutover baseline check, the exact cutover step, the three before/after assertions to verify,
  the rollback command, and the sign-off ("all three green → migrated").
- `no-outage-proof.md` — the **proof (logs)** that no app had an outage: per cohort, the before capture
  (200 via VPN) and the after capture (200 via proxy + the proxy allow-log line + the injected identity
  header + the now-denied unauth request + the now-closed direct-to-backend probe), plus the final
  all-apps post-decommission capture.
- `rollback-note.md` — the per-cohort rollback command, with the one capture proving a cohort came back on
  the old path after a rollback was actually run.

Do **not** commit: any TLS material / keys Pomerium generates at runtime, the VPN/WireGuard keys or
configs the legacy stand-in generates, raw container logs beyond the curated proof lines, or the lab's
seeded app data (it lives in the lab repo, not yours).

## Automate & own it
**Required — this is the before/after access test turned into a reusable cutover gate.** A migration you
can't *re-prove* is a migration you don't actually trust. Build the access test into a harness,
`access-test.sh <app>`, that a model drafts and **you review every line of**, asserting the three
conditions for one app and exiting non-zero on any failure:
1. **(a) No outage:** an authorized (valid-JWT) request to the app returns **200**.
2. **(b) Via the proxy:** the same request shows the proxy-injected identity header in the backend echo
   **and** an *unauthenticated* request returns **non-200** (identity is now enforced).
3. **(c) Old path closed:** a **direct** request to the backend on the flat network **fails to connect**.

Wire it as the `make cutover` gate (run automatically after each cohort flip) and as a `make verify`
target that runs it across **all** apps — so "prove every migrated app is still no-outage, proxied, and
flat-path-closed" is one command anyone can run, including after the decommission. **Review every line**:
confirm each assertion **fails closed** — a check that errors (the harness itself broke, a timeout) must
count as a *failure*, never a silent pass — and confirm (c) actually distinguishes "connection refused"
(good: path closed) from "the test couldn't run" (not a pass). The most dangerous bug here is a harness
that goes green when it merely *couldn't reach* the backend, reading a broken test as a closed path.
(AI drafts; you prove the signal is honest and you own it.)

## AI acceleration
Ask a model to draft the per-app cutover checklist and the `access-test.sh` harness — then refuse to trust
its plan. The model's default instinct is **big-bang**: ask it to "migrate the apps to ZTNA" and it will
hand you one flip for everything, because that's the simplest thing to express and it carries none of the
operational fear of a live outage. The judgment it cannot do for you is **sequencing by blast radius**
(which cohort is safe first, its dependencies, who to coordinate with) and **verifying the third
assertion** — asked to "confirm the migration worked," a model checks that the app answers through the
proxy and calls it done, missing the open flat path entirely. Make it draft the checklist and the harness;
**you** decide the cohort order, confirm every cohort has a *tested* rollback, and verify the proof shows
no-outage *and* old-path-closed for each app before the VPN comes down. Then ask it: "what could still
reach this backend around the proxy?" — and verify each answer against an actual direct probe, not the
model's claim.

## Connects forward
This is the brownfield reality that makes the rest of the track real. The *new path* you migrate **to** is
the identity-aware proxy from **Module 06** — this module is "now do it to a network that's already
running and can't go down." The **no-bypass / trust-only-the-proxy** discipline from Module 06 is exactly
what assertion (c) enforces per cohort: closing the flat path is the org-wide version of "every path to
the backend must pass through the proxy." Once the estate is behind the proxy, **Module 07
(Microsegmentation)** is the next layer — default-deny *between* the now-migrated services, so identity at
the front door is paired with segmentation in the interior (the two halves of un-flattening the network
Module 01 indicted). And the migrated, proxied estate is the system the **Red-team-your-own-deployment**
module (Type 10) attacks end-to-end — including retrying the very bypass your assertion (c) just closed.

## Marketable proof
> "I migrate a brownfield VPN to identity-aware (ZTNA) access without downtime — strangler-fig, one cohort
> at a time: stand the proxy beside the running VPN, cut each cohort over behind a DNS/feature-flag switch,
> and prove every move with a before/after access test that asserts three things — the app is still
> reachable (no outage), it's now reached *through the proxy* (identity enforced per request), and the old
> flat path is *closed* (no direct-to-backend bypass). Every cohort has a tested rollback, the VPN comes
> down only after the last cohort is provably across, and I can explain why a migration is done when the
> old path is *closed*, not merely when the new one *works* — and why big-bang cutovers fail."

## Stretch
- **Cohort by *identity*, not just by app:** cut a cohort over by IdP group (move the "engineering" group
  to the proxy while "finance" stays on the VPN for the same app), so the cutover switch is a per-group
  access policy — the more realistic enterprise rhythm — and prove the two groups take different paths to
  the same service during the overlap.
- **A dependency that breaks the naive order:** add an app that calls *another* app over the flat network;
  migrate them in the wrong order on purpose, watch the dependency break, then re-sequence — proving why
  blast-radius/dependency ordering is the judgment, not a formality.
- **Verify the assertion in the backend for real:** swap one backend for a tiny app that validates
  `X-Pomerium-Jwt-Assertion` against Pomerium's JWKS (the Module 06 stretch), then confirm that after
  cutover the app trusts *only* the signed assertion — so even a leftover flat-path request with a forged
  header is refused. This makes assertion (c) airtight at the app layer, not just the network layer.

---

## Lab-env spec (to be built at promotion)

*This module has no `plaintext-labs` directory yet; build it at promotion under
`plaintext-labs/ztna/<NN>-vpn-ztna-migration/` (final `<NN>` per the placement decision — insert between
06 and 07 and renumber, or land as the Phase-3 project). Reuse Module 06's Pomerium env as the new path so
it runs with zero cloud cost. It must contain:*

- **The two paths, side-by-side, in `docker-compose.yml`** — (1) a **legacy/flat path**: a small set of
  app backends (~3, e.g. `whoami`-style or tiny HTTP services on distinct hostnames) on a **flat Docker
  network**, plus a **"VPN client" container** (a WireGuard/Headscale node *or* a plain client on that
  flat network — a flat-network stand-in is acceptable per the brief) that can reach each backend directly
  by internal hostname, no identity check; and (2) a **new path**: **Pomerium** (the Module 06 all-in-one
  proxy with the built-in mock IdP) in front of the *same* backends, on a network where the backends have
  **no published port**. At `make up`, each app is reachable the legacy way; the proxy path comes online
  per cohort.
- **The cutover mechanism (`make cutover COHORT=n` / `make rollback COHORT=n`)** — a per-cohort switch that
  flips an app's resolution between the flat route and the proxy. Implement as a **DNS change** (rewrite
  the client's resolver / `/etc/hosts` entry for `appN.internal` to point at Pomerium instead of the flat
  backend) or a **feature flag** the proxy/router reads. `cutover` must *also* **close the flat route** for
  that app (drop the backend off the flat network / firewall the direct path) so assertion (c) can pass;
  `rollback` reverses both (restore the flat route, point DNS back). Both idempotent and re-runnable.
- **The before/after access-test harness (`access-test.sh <app>`)** — the `make demo`/`make verify`
  equivalent and the success signal: asserts the three conditions — (a) authorized request → 200, (b)
  proxy-injected identity header present + unauth → non-200, (c) direct-to-backend on the flat network →
  connection refused/closed — and **fails closed** (a broker/timeout error counts as failure, never a
  silent pass; (c) distinguishes "refused" from "couldn't run"). It should *pass for migrated cohorts and
  fail for not-yet-migrated ones*, and pass for *all* apps after `make decommission`.
- **`make decommission`** — closes the flat network / stops the VPN-client's direct reach to every backend
  (the final org-wide version of the per-cohort flat-path close), runnable only meaningfully once every
  cohort is across; `make verify` after it must show all apps still 200 via the proxy and zero flat reach.
- **`Makefile`** — `up` / `demo` / `cutover` / `rollback` / `verify` / `decommission` / `shell` / `down`
  (+ a `reset` that returns to the all-on-VPN baseline). Pomerium + mock IdP as in Module 06 (no real IdP
  account; `@example.com` tokens).
- **CI note:** parts are CI-runnable (`make up`, cutover one cohort, `make verify` passes for it), but the
  full lab is a **learner exercise** (the success state requires the learner to drive each cohort and close
  each flat path) — so add `.ci-demo` only if a scripted "cutover-cohort-1 → verify-green" smoke path is
  wired and green on a Linux runner; otherwise leave it off (learner-exercise lab, like Module 06's gate
  and the click-ops→IaC migration lab).
