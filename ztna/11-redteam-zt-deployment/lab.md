# Lab 11 — Red-team Your Zero-Trust Deployment

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 10 · Design → red-team-your-own-design → harden.** You already built the gated service (Modules
05/06). Here you **attack your own design** with four probes, document the ones it refuses (the design
held — that *is* the evidence), and for the one that lands against a deliberately-naive backend, harden
it and re-attack until it fails too. The deliverable is the four documented attacks + the hardening
diff. No grader; you verify your own work against the observable success criteria below. (Honor system:
the committed report, the hardening diff, and the re-runnable harness are the proof.)

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It reuses the Module 06
Pomerium environment and adds a second, deliberately-vulnerable backend plus an attack harness:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/redteam-zt-deployment
make up       # Pomerium (all-in-one + mock IdP) + a VERIFYING backend + a NAIVE backend
make attack   # run all four attacks and print a per-attack PASS (refused) / FAIL (got through) report
make shell    # drop into the attacker container for manual probing
make down     # stop everything
```

The environment starts:
- **Pomerium** (all-in-one mode with a built-in mock IdP) on port 8443 — the same proxy you built in 06.
- **`whoami-verifying`** — a small backend that fetches Pomerium's JWKS and validates
  `X-Pomerium-Jwt-Assertion` (signature, `aud`, `iss`, `exp`) before trusting any identity. On an
  internal Docker network with **no published port**.
- **`whoami-naive`** — a deliberately-vulnerable backend that reads a *plain* `X-Forwarded-User`
  header and believes it (the header-trust mistake from the module). Routed behind Pomerium too, so the
  forgery attack has something to actually succeed against — the finding you harden.
- An **attacker** container (with `nmap`/`curl`) on a separate network, used by `make attack`.

> **Authorization note.** Every attack in this lab is aimed *only at your own lab deployment*, running
> locally in Docker. Only ever scan or attempt to reach systems you own or have explicit written
> permission to test. Do not point `attack.sh`, `nmap`, or any probe at a host you do not own.

## Scenario

You stood up an identity-aware proxy (Module 06) and a no-inbound-ports published service (Module 05).
Leadership says "we've deployed Zero Trust." Your job is to prove it — or find where it isn't. You will
attack your own deployment the way an outsider would, and produce the evidence a security review asks
for: the attacks it refused, and the one weakness you found and fixed. A refused attack is a documented
win; the finding you land and harden is the exercise working.

## Do

Run each of the four attacks, record PASS (refused, with the evidence) or FAIL (got through), then
harden the one that fails and re-attack until it's refused too.

**Attack 1 — prove nothing listens (no inbound)**
1. [ ] **External port scan.** From the attacker container (`make shell`), scan the proxy host and
   confirm only the proxy's port answers — and crucially that the *backends* expose nothing:
   ```bash
   nmap -Pn -p- pomerium        # the proxy: 8443 open, expected
   nmap -Pn -p- whoami-naive whoami-verifying   # the backends: NO open ports
   ```
   Record the result. The backends must have no published port — the connector/proxy is the only thing
   that listens. (Goal: there is no service to fingerprint or reach around the proxy.)

**Attack 2 — prove an unauthenticated request is denied**
2. [ ] **No-session request.** Send a request with no token and confirm it never reaches a backend:
   ```bash
   curl -sk https://pomerium:8443/ -o /dev/null -w "%{http_code}\n"
   ```
   You must get a redirect (302) or access-denied — **never a 200 with backend content**. Record the
   code and (if any) the redirect target. (Goal: identity is required on every request, not once.)

**Attack 3 — forge the proxy's identity headers (the centerpiece)**
3. [ ] **Forge a client-supplied identity header at both backends.** This is the CVE-2026-40575 class:
   a header an attacker can also set, trusted as if the proxy set it. Send a forged identity and see
   which backend believes it:
   ```bash
   # against the VERIFYING backend — must be refused
   curl -sk https://pomerium:8443/verifying/ \
     -H "X-Pomerium-Jwt-Assertion: forged.jwt.value" \
     -H "X-Forwarded-User: admin@example.com"
   # against the NAIVE backend — this is your finding
   curl -sk https://pomerium:8443/naive/ \
     -H "X-Forwarded-User: admin@example.com"
   ```
   Document for each backend: did your forged header reach it, and did it *act* on the identity? The
   verifying backend must reject the forged assertion (it isn't signed by Pomerium's key); the naive
   backend will impersonate `admin@example.com` — that is the finding you'll harden.
4. [ ] **Name the rule and the finding.** In `redteam-report.md`, write the backend's rule in one
   sentence: *trust the identity in `X-Pomerium-Jwt-Assertion` only after verifying its signature
   against Pomerium's JWKS (`/.well-known/pomerium/jwks.json`) plus `aud`/`iss`/`exp`; never trust a
   plain, client-supplied identity header.* Then record the finding: `whoami-naive` trusts an unsigned
   `X-Forwarded-User`, so a free `curl -H` impersonates any user.

**Attack 4 — bypass the proxy straight to the backend**
5. [ ] **Try to reach a backend directly.** From the attacker container, attempt to connect to the
   backend on its service port without going through Pomerium:
   ```bash
   curl -s --max-time 5 http://whoami-naive/ -o /dev/null -w "%{http_code}\n" || echo "unreachable"
   ```
   It must be unreachable (no route / connection refused / timeout) — every path in goes through the
   proxy. Record the result. (Goal: bypass is the dual of denial; a reachable backend makes the deny
   path moot.)

**Harden the finding and re-attack**
6. [ ] **Harden the naive backend.** Change `whoami-naive` so it verifies the signed assertion (or
   strips/ignores the client `X-Forwarded-User` and reads only `X-Pomerium-Jwt-Assertion` after JWKS
   verification). The lab ships a `data/verify_assertion.py` reference you can wire in — read it, don't
   just paste it. `make down && make up`.
7. [ ] **Re-attack until it fails.** Re-run Attack 3 against the now-hardened backend; the forged
   `X-Forwarded-User` must no longer impersonate anyone. Capture the before (200 as `admin`) and after
   (rejected) — that diff is the deliverable's core.

## Success criteria — you're done when

- [ ] **Attack 1:** `nmap` shows the backends with **no open ports**; only the proxy listens. Recorded.
- [ ] **Attack 2:** the no-session request returns a non-200 (redirect/denied), never backend content.
- [ ] **Attack 3:** the **verifying** backend refuses the forged identity header; the **naive** backend
      is shown to be fooled by it (the finding), and the backend's verify-the-signed-assertion rule is
      written down.
- [ ] **Attack 4:** a direct-to-backend request is unreachable — no proxy bypass exists.
- [ ] **Harden + re-attack:** after hardening, the same forgery against the previously-naive backend is
      refused; you captured the before/after.
- [ ] `make attack` reports PASS for attacks 1, 2, 4 and the verifying half of 3 on the shipped design,
      and goes **red** when pointed at the naive backend pre-hardening (proving the harness can tell).

*Honor system: there is no grader. These are observable — an `nmap` with no open backend ports, a
non-200 unauth response, a forged-header impersonation that flips from succeed to refused after
hardening, an unreachable direct-to-backend probe. Check your own work honestly against them.*

## Deliverables

- `redteam-report.md` — the four attacks, each with the command run, the observed result, and a
  PASS (refused — the design held) / FINDING verdict. Include the backend's header-trust rule, the
  naive-backend finding, and the before/after of the hardening.
- The **hardening diff** — the change to `whoami-naive` (or its config) that makes it verify the signed
  assertion / stop trusting the client header, committed alongside the report.
- `attack.sh` + the `make attack` target (see *Automate & own it*).

Commit all three. Lab artifacts (TLS material Pomerium generates at runtime, scan output dumps) stay
out of commits — they're in `.gitignore`.

## Automate & own it

**Required — turn the four manual attacks into one re-runnable harness.** Write `attack.sh` that:
1. Runs the external port scan and asserts the backends have **no open ports** (only the proxy listens).
2. Asserts the unauthenticated request to the proxy is **NOT** a 200.
3. Sends the forged identity header and asserts the **verifying** backend refuses it; runs the same
   forgery against the **naive** backend and reports whether it was impersonated (the finding).
4. Attempts the direct-to-backend bypass and asserts it is **unreachable**.
5. Prints a per-attack PASS/FAIL/FINDING line and exits 0 only if every *should-fail* attack was refused.

Have a model draft it; **you read every line**, hunting the one failure mode that matters in a red-team
harness: it must **fail closed**. A `curl` that returns `000`, times out, or hits an unexpected redirect
must count as a result-to-investigate, never a silent PASS — otherwise the harness tells you the design
held when your *test* broke. Prove the harness honest by pointing it at the naive backend before you
harden it and confirming it goes red. Wire it as `make attack`: this is your deployment's standing
red-team — a future config change that publishes a backend port, trusts a client header, or opens the
unauth path must turn `make attack` red.

## AI acceleration

Ask a model to draft `attack.sh` and the forged-header payloads from a plain-English description of the
four attacks — it's fast and mostly right. Then refuse to trust the green: review every assertion for
fail-open behavior (a probe that errors must not report PASS), and confirm the harness actually
distinguishes a held design from a broken test by running it against the deliberately-naive backend. The
transferable skill isn't prompting for `nmap` flags; it's owning a red-team harness whose PASS you can
defend — because you watched it correctly fail.

## Connects forward

This module is the integration point for the deny-path discipline built across the track. The
no-inbound-ports proof generalizes Module 05's external-probe step; the forged-header and bypass attacks
generalize Module 06's `check-deny.sh` into a whole-deployment red-team. The signed-assertion rule you
enforce here is what **Module 08 (Policy as Code / OPA)** evaluates for fine-grained authorization, and
the standing `make attack` harness is the natural input to **Module 09 (Monitoring & Detection)** — each
refused attack should also *fire a detection*. As a Phase-3, capstone-adjacent module, the
`redteam-report.md` is the evidence artifact the track's capstone deployment is judged against.

## Marketable proof

> "I red-team my own Zero-Trust deployment before I call it done: I prove nothing listens with an
> external scan, prove the unauthenticated path is denied, attempt to forge the proxy's signed identity
> assertion and to bypass the proxy straight to the backend — and I document the attacks that failed as
> evidence the design holds. When I find a backend that trusts a client-supplied identity header (the
> CVE-2026-40575 class), I harden it to verify the proxy's signed assertion and re-attack until the
> forgery fails, with a standing harness that goes red the moment the deny path reopens."

## Stretch

- **Forge a *signed* assertion the hard way.** Pull Pomerium's JWKS, observe you can read the public key
  but not the private one, and articulate precisely why you cannot mint a valid `X-Pomerium-Jwt-Assertion`
  — the asymmetry that makes the signed assertion the actual security boundary.
- **Bypass via a flat network.** Add the naive backend to a shared Docker network with a published port
  (simulating the "teammate ran `docker run -p` for convenience" mistake), prove the bypass now works,
  then close it — the real-world way Attack 4 gets reintroduced after a clean deploy.
- **Chain to detection.** Tee `attack.sh`'s probes into Pomerium's access logs and write one Sigma rule
  that fires on the forged-header / direct-bypass pattern (the bridge into Module 09).

---

## Lab-env spec — to build at promotion (`plaintext-labs/ztna/<NN>-redteam-zt/`)

*This section is the build brief for the runnable environment; it is not learner-facing prose and is
removed/relocated when the lab env is built and validated. Reuses the Module 06 Pomerium env.*

**Layout** (`plaintext-labs/ztna/<NN>-redteam-zt/`):
- `docker-compose.yml` — services:
  - `pomerium` — reuse the Module 06 all-in-one Pomerium image + mock IdP (copy `06-identity-aware-access/data/config.yaml`), exposing **only** 8443. Add two routes: `/verifying/` → `whoami-verifying`, `/naive/` → `whoami-naive`, both with `pass_identity_headers: true`.
  - `whoami-verifying` — a tiny backend (Python/Flask or a small Go service) that, on every request, fetches `https://pomerium:8443/.well-known/pomerium/jwks.json`, validates `X-Pomerium-Jwt-Assertion` (signature, `aud`, `iss`, `exp`), and returns 200 + identity only on a valid assertion; 401 otherwise. **No published port.**
  - `whoami-naive` — the same shape but deliberately wrong: trusts a plain `X-Forwarded-User` header and echoes/acts on it with no verification. **No published port.** This is the target the forgery succeeds against.
  - `attacker` — a small image with `nmap`, `curl`, `jq`, on a **separate** Docker network that can reach `pomerium:8443` but is **not** on the backends' internal network (so Attack 4's direct probe genuinely can't route).
- `data/`:
  - `config.yaml` — Pomerium config with the two routes (copied/adapted from 06).
  - `verify_assertion.py` — the reference JWKS-verification helper the learner wires into `whoami-naive` during the hardening step (PyJWT + JWKS fetch; documented, reviewable).
- `attack.sh` — the four-attack harness (also the learner deliverable target; ship a reference copy that **fails closed**).
- `Makefile` — `up` / `down` / `reset` / `shell` / **`attack`** (runs `attack.sh` inside the `attacker` container and prints the per-attack PASS/FAIL/FINDING report) / `demo` (alias that runs `make up && make attack`).
- `.gitignore` — Pomerium runtime TLS material, any `*.nmap`/scan dumps, tokens.

**Validation bar (before promotion):** `make up && make attack && make down` runs green on a Linux
runner with the **shipped** design (attacks 1, 2, 4 and the verifying half of 3 all refused); and
`make attack` correctly reports the **FINDING** against `whoami-naive` pre-hardening and flips to PASS
after the learner wires in `verify_assertion.py`. Because the lab includes a known-vulnerable backend,
the harness is self-checking — it must distinguish a held design from a broken test. Add the `.ci-demo`
marker only once the shipped-design run is green; the learner-hardening path stays a learner exercise.
