# Lab 11 — Red-team Your Zero-Trust Deployment: attack it, harden it, regression-test it

> **Hands-on lab.** Objective: **attack the gated service you built in Modules 05/06,
> document what it refuses, harden the one gap that lands, and freeze every attack into a regression
> suite.** Target: **~2–3 hrs**, one finish line. This lab **reuses the Module 06 Pomerium environment**
> you already stood up — it does *not* ship a new container stack. (Honor system: the committed report,
> the hardening diff, and the re-runnable harness are the proof.)

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A control you haven't attacked is a hope.** | A green dashboard proves the happy path, never the deny path. |
| 2 | **Enumerate the assumptions:** nothing listens · no unauth reach · no forged identity · no bypass. | Each promise is one attack; a design you can list you can regression-test. |
| 3 | **Header forgery is the centerpiece.** | `curl -H "X-Forwarded-User: admin"` is free; a *signed* `X-Pomerium-Jwt-Assertion` needs the proxy's key. |
| 4 | **The backend's rule:** trust only the signed assertion, verified vs JWKS + `aud`/`iss`/`exp`. | This is what CVE-2026-40575 (CVSS 9.1) got wrong — a client-set header trusted as truth. |
| 5 | **A refused attack is a documented WIN.** | "I attacked this and it held" is the artifact a review asks for — the finding you land is the exercise working. |
| 6 | **Every attack becomes a regression check.** | A gap found once but never re-tested ships again; the harness must fail *closed*. |

*(If you can explain all six cold at the end — especially #6 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea + attack-surface table](README.md#the-core-idea) and the
> [header-forgery centerpiece](README.md#the-centerpiece-identity-header-forgery).

---

## Warm-up — answer before you read on (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Your Module 06 Pomerium deployment returns a green health check and a `connected` tunnel. Name the
   **four** things that being green does *not* prove — one per trust assumption.
2. Why does `curl -H "X-Forwarded-User: admin@corp.com"` cost an attacker nothing, while forging
   `X-Pomerium-Jwt-Assertion` is infeasible? What exactly does the attacker lack?

---

## Setup

This lab **reuses the environment you already built in Module 06** — the all-in-one Pomerium proxy in
front of a `whoami` backend that has **no published port**. You do not stand up a new stack; you turn
the deployment you own into a target.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/06-identity-aware-access
make up        # Pomerium on :8443 + a whoami backend reachable ONLY through Pomerium
```

To have something the identity-forgery attack can actually *succeed* against, you'll add a second,
**deliberately-naive** route/backend yourself during Step 3 (attacker→fixer: you build the weakness so
you can find and fix it). Keep it tiny — a `traefik/whoami` (which echoes every header it receives back
in the body) behind a Pomerium route with `pass_identity_headers: true` is enough to *observe* a
client-set header reaching the backend; the "naive backend" is the assumption that a real service would
*act* on that echoed header. You run the attacks from a throwaway container with `nmap`/`curl`:

```bash
docker run --rm -it --network ztna-lab_ztna-lab \
  ghcr.io/plaintext-security/attacker:latest sh   # or any image with nmap + curl + jq
```

> **⚠ Authorization — read this before you scan anything.** Every probe in this lab is aimed **only at
> your own local lab deployment**, running in Docker on your machine. Port-scanning, header-forging, or
> bypass-probing a host you do **not** own — or do not have **explicit written permission** to test — is
> an attack, and in most jurisdictions a crime. Do not point `nmap`, `curl`, or any harness at a
> production system, a cloud endpoint, a coworker's box, or any address outside `ztna-lab`. The whole
> value of this module is that the target is *yours*.

---

## Scenario

You stood up an identity-aware proxy (Module 06) in front of a no-inbound-ports published service
(Module 05). Leadership says "we've deployed Zero Trust." Your job is to prove it — or find where it
isn't. You'll attack your own deployment the way an outsider would, produce the evidence a security
review asks for (the attacks it refused, and the one weakness you found and fixed), and — the part that
outlives the report — leave behind a **regression suite** so a future config change that reopens a deny
path fails loudly before it ships.

---

## Build it — read a little, do a little

Run each attack, record **PASS** (refused, with the evidence) or **FINDING** (got through), then harden
the one that lands and re-attack. As you go, write each probe into `attack.sh` — you are building the
regression suite as you red-team, not after.

### Step 1 — Prove nothing listens (no inbound listener)

**Concept (30 sec):** Flight-card #2. The backend dialed *out* or has no published port; the proxy is
the only thing that answers. If a backend exposes a port, there's a service to fingerprint and reach
*around* the proxy — and the whole model is moot.

**Do it:** from the attacker container, scan the proxy and the backend. The proxy's `8443` should
answer; the backend should expose **nothing**.

```bash
nmap -Pn -p- pomerium        # proxy: 8443 open, expected
nmap -Pn -p- whoami          # backend: NO open ports
```

> **▸ On track if:** `nmap` reports the backend with **no open ports** and only the proxy listening.
> Record the raw output as evidence. If the backend shows an open port, you found Attack 4 early — note
> it.

### Step 2 — Prove an unauthenticated request is denied (verify explicitly)

**Concept (30 sec):** Flight-card #2. Identity is required on *every* request, not once at a login. A
no-session request must land on a redirect or a drop — never a 200 with backend content.

**Do it:** send a request with no token and read the status code.

```bash
curl -sk https://pomerium:8443/ -o /dev/null -w "%{http_code}\n"
```

> **▸ On track if:** you get a **302** (redirect to the IdP) or an access-denied — **never a 200** with
> `whoami` content. Record the code and any redirect target. A 200 here means the deny path is open and
> the later attacks don't matter yet — fix Module 06 first.

### Step 3 — Forge the proxy's identity header (the centerpiece)

**Concept (30 sec):** Flight-card #3 + #4. This is the CVE-2026-40575 class: a header the attacker can
*also* set, trusted as if the proxy set it. A verifying backend checks the *signed* `X-Pomerium-Jwt-Assertion`
against the JWKS; a naive backend believes a plain `X-Forwarded-User`.

**Do it:** first add your deliberately-naive route (see Setup) so you have both a verifying and a naive
target. Then send a forged identity to each and watch which one believes it.

```bash
# against a verifying route — must be refused (forged assertion isn't signed by Pomerium's key)
curl -sk https://pomerium:8443/verifying/ \
  -H "X-Pomerium-Jwt-Assertion: forged.jwt.value" \
  -H "X-Forwarded-User: admin@example.com"
# against your naive route — this is your finding
curl -sk https://pomerium:8443/naive/ \
  -H "X-Forwarded-User: admin@example.com"
```

Then, in `redteam-report.md`, write the backend's rule in one sentence: *trust the identity in
`X-Pomerium-Jwt-Assertion` only after verifying its signature against Pomerium's JWKS
(`/.well-known/pomerium/jwks.json`) plus `aud`/`iss`/`exp`; never trust a plain, client-supplied
identity header.* Record the finding: the naive route echoes/acts on an unsigned `X-Forwarded-User`, so
a free `curl -H` impersonates any user.

> **▸ On track if:** the **verifying** route rejects the forged assertion, and the **naive** route is
> shown to be fooled by the raw header (your finding). If *both* refuse it, your naive route isn't
> actually reading the client header — re-check that `pass_identity_headers` is on and the backend reads
> `X-Forwarded-User`. If *both* accept it, the proxy is stripping nothing — that's a bigger finding.

### Step 4 — Bypass the proxy straight to the backend (the dual of denial)

**Concept (30 sec):** Flight-card #2. Even a perfect deny path is decoration if the backend is reachable
without traversing the proxy. Every path in must go through Pomerium.

**Do it:** from a network the backend does *not* share (or by naming the backend service directly),
attempt to reach it without the proxy.

```bash
curl -s --max-time 5 http://whoami/ -o /dev/null -w "%{http_code}\n" || echo "unreachable"
```

> **▸ On track if:** the direct request is **unreachable** (no route / connection refused / timeout) —
> every path in goes through the proxy. If it answers, you've found a bypass: the backend is on a
> reachable network or publishing a port. Record it and close it.

### Step 5 — Harden the finding and re-attack

**Concept (30 sec):** Flight-card #5. The finding is the exercise working. Hardening + re-attacking until
the same forgery fails is the deliverable's core.

**Do it:** change the naive route so it verifies the signed assertion (or strips/ignores the client
`X-Forwarded-User` and reads only `X-Pomerium-Jwt-Assertion` after JWKS verification). A small
PyJWT-based verifier that fetches `/.well-known/pomerium/jwks.json` and validates signature + `aud` /
`iss` / `exp` is enough — *read* what it does, don't just paste it. Restart, then re-run the Step 3
forgery.

> **▸ On track if:** you captured the **before** (200 as `admin@example.com`) and the **after**
> (rejected) of the exact same forged request. That diff is what proves the fix, not your say-so.

---

## Prove the control (your finish line)

Assemble `redteam-report.md` (the four attacks, each with the command, the observed result, and a
PASS / FINDING verdict; plus the header-trust rule and the before/after hardening diff). Then run the
**one check that proves the whole thing is real**:

> **Point your `attack.sh` harness at the *naive* route before you harden it and confirm it goes RED;
> re-run it after hardening and confirm every should-fail attack is PASS.**

That is the finish line: **every gap you found now has a committed regression check that (a) refuses the
attack on the hardened design and (b) demonstrably went red against the known-vulnerable target.** A
harness that stays green against the naive backend is a harness that would never catch a regression —
so it is the harness, not the design, that failed. Fix it until it correctly goes red, then trust its
green.

---

## Recall check — close the doc, answer from memory (3 min)

1. Name the four trust assumptions and the one attack that tests each.
2. What is the backend's exact rule for trusting an identity header, and which CVE this year is the
   failure to follow it?
3. What does "failing open" mean in a red-team harness, and why is it *worse* once the check is a
   standing regression test?

Missed one? Re-run the step that built it, or pull the [module core idea](README.md#the-core-idea) —
then re-answer.

---

## Deliverables

- **`redteam-report.md`** — the four attacks, each with the command run, the observed result, and a
  PASS (refused — the design held) / FINDING verdict. Includes the backend's header-trust rule, the
  naive-backend finding, and the before/after of the hardening. A portfolio artifact: it shows you can
  attack a Zero-Trust deployment, distinguish a held design from a broken test, and fix what you find.
- **The hardening diff** — the change that makes the naive route verify the signed assertion / stop
  trusting the client header, committed alongside the report.
- **`attack.sh` (the regression suite)** — the re-runnable harness (see *Automate & own it*).

Commit all three. Lab artifacts (TLS material Pomerium generates at runtime, `*.nmap` scan dumps,
tokens) stay out of commits — they're in `.gitignore`.

## Automate & own it

**Required — the regression suite *is* the automation.** Turn the four manual attacks into one
re-runnable `attack.sh` that:

1. Runs the external port scan and asserts the backend has **no open ports** (only the proxy listens).
2. Asserts the unauthenticated request to the proxy is **NOT** a 200.
3. Sends the forged identity header and asserts the **verifying** route refuses it; runs the same
   forgery against the **naive** route and reports whether it was impersonated (the finding).
4. Attempts the direct-to-backend bypass and asserts it is **unreachable**.
5. Prints a per-attack PASS / FINDING line and **exits non-zero if any should-fail attack got through**.

Have a model draft it; then **you read every line**, hunting the one failure mode that matters in a
red-team harness: it must **fail closed**. A `curl` that returns `000`, times out, or hits an unexpected
redirect must count as a result-to-investigate, never a silent PASS — otherwise the harness tells you
the design held when your *test* broke. Prove the harness honest by pointing it at the naive route
before you harden it and confirming it goes red. This is your deployment's **standing red-team**: wire
it so a future config change that publishes a backend port, trusts a client header, or reopens the
unauth path turns `attack.sh` red before it merges.

## Definition of done (`redteam-zt` ✅)

- [ ] **Attack 1:** `nmap` shows the backend with **no open ports**; only the proxy listens. Recorded.
- [ ] **Attack 2:** the no-session request returns a non-200 (redirect/denied), never backend content.
- [ ] **Attack 3:** the verifying route refuses the forged header; the naive route is shown fooled (the
  finding), and the backend's verify-the-signed-assertion rule is written down.
- [ ] **Attack 4:** a direct-to-backend request is unreachable — no proxy bypass exists.
- [ ] **Harden + re-attack:** after hardening, the same forgery is refused; you captured the before/after.
- [ ] **`attack.sh`** reports PASS for the hardened design and demonstrably went **red** against the
  naive route pre-hardening (the harness can tell a held design from a broken test), and fails closed.
- [ ] `redteam-report.md` + the hardening diff + `attack.sh` are committed; you can explain all six
  flight-card facts cold.

## Connects forward

This module is the integration point for the deny-path discipline built across the track. The
no-inbound-ports proof generalizes Module 05's external-probe step; the forged-header and bypass attacks
generalize Module 06's deny checks into a whole-deployment red-team. The signed-assertion rule you
enforce here is what **Module 08 (Policy as Code / OPA)** evaluates for fine-grained authorization, and
your standing `attack.sh` is the natural input to **Module 09 (Monitoring & Detection)** — each refused
attack should also *fire a detection*. As the capstone-adjacent module, `redteam-report.md` is the
evidence artifact the track's capstone deployment is judged against.

## Marketable proof

> "I red-team my own Zero-Trust deployment before I call it done: I prove nothing listens with an
> external scan, prove the unauthenticated path is denied, attempt to forge the proxy's signed identity
> assertion and to bypass the proxy straight to the backend — and I document the attacks that failed as
> evidence the design holds. When I find a backend that trusts a client-supplied identity header (the
> CVE-2026-40575 class), I harden it to verify the proxy's signed assertion and re-attack until the
> forgery fails — then I freeze every probe into a standing regression suite that goes red the moment a
> deny path reopens."

## Stretch

- **Forge a *signed* assertion the hard way.** Pull Pomerium's JWKS, observe you can read the public key
  but not the private one, and articulate precisely why you cannot mint a valid `X-Pomerium-Jwt-Assertion`
  — the asymmetry that makes the signed assertion the actual security boundary.
- **Reintroduce the bypass.** Add the backend to a shared network with a published port (the "teammate
  ran `docker run -p` for convenience" mistake), prove the bypass now works, close it — and confirm your
  `attack.sh` catches the regression automatically.
- **Chain to detection.** Tee `attack.sh`'s probes into Pomerium's access logs and write one Sigma rule
  that fires on the forged-header / direct-bypass pattern (the bridge into Module 09).
