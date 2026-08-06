# Lab 10 — VPN → ZTNA Migration: plan a brownfield cutover, cohort by cohort, with no outage

> **Hands-on lab** (design / paper — no containers). Objective: **produce a strangler-fig migration runbook that takes
> a running VPN off a flat network and behind an identity-aware proxy, one cohort at a time, with no
> outage.** Target: **~90–120 min** for the plan, one finish line. This is a **design / paper lab — no
> containers.** You are writing the plan an on-call engineer could execute Monday, not standing up an
> environment. (The runnable Docker version — Pomerium beside a flat-network stand-in — is deferred to a
> later env build; this edition works the design end so it's decoupled from that.)

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Brownfield, not greenfield.** The VPN already runs; the whole org logs in every morning. | "Just stand up ZTNA" is greenfield advice. The constraint that defines the job is *no outage*. |
| 2 | **Big-bang is the trap.** Flip everything one Saturday, VPN off. | Every path changes at once → one blast radius, no per-slice rollback, debugged as a total outage. |
| 3 | **Strangler-fig: run both, move one cohort at a time.** | Publish behind the proxy beside the running VPN; a per-cohort DNS/flag switch picks the path. Moving cohort 1 touches nothing else. |
| 4 | **The before/after test proves THREE things.** | (a) still reachable — no outage; (b) now *via the proxy* — identity enforced; (c) old flat path *closed* — no bypass. |
| 5 | **Done = old path CLOSED, not new path WORKS.** | Leaving the flat route open is migration theater; every user and attacker can still skip the proxy. #4(c) is the one teams skip. |
| 6 | **Rollback is cheap; decommission is last.** | Back a cohort out by flipping to the VPN route (still running). Kill the VPN only when the un-migrated surface is provably zero. |

*(If you can explain all six cold at the end — especially #4(c) and #5 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea-you-dont-flip-a-switch-you-run-both-move-cohorts-prove-each-then-retire-the-vpn)
> and the [case for retiring the VPN](README.md#the-case-for-retiring-the-vpn-a-vpn-appliance-is-a-single-fat-target).

---

## Warm-up — answer before you read the estate (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Name the **two** distinct reasons to retire a legacy VPN — one about the *access model* (Module 01),
   one about the *appliance itself* (the case section). Which one does ZTNA's "no inbound port on the
   backend" posture directly delete?
2. You cut one app over to the proxy and it answers 200 through the proxy. Your teammate says "migrated."
   What **third** thing must you check before you agree — and what does skipping it leave open?

---

## Setup

**No containers.** You work from the brownfield estate below (a fictional firm) and produce a migration
plan. There is nothing to `git clone` or `make` — the deliverable is the runbook, checklist, and
rollback plan, plus a small script you run against an inventory file.

The estate you are migrating (`estate.md`, reproduced here so you can reason about it):

| App | Users | Sensitivity | Dependencies | Notes |
|---|---|---|---|---|
| `wiki.internal` | one product team (~12) | low | none | team wiki; the team can coordinate a 5-min window |
| `dash.internal` | ~120 staff | medium | reads from `wiki.internal` over the flat net | internal metrics dashboard |
| `admin.internal` | 4 admins + 1 vendor | **high** | none | legacy admin tool; the vendor connects from a fixed source range |
| `ci-artifacts.internal` | CI runners (no human) | medium | pulled by `dash.internal` builds | service-account auth, no interactive login |

Today every one of these is reached by *being on the VPN's flat network* — connectivity is the only
check. Your new path is the identity-aware proxy from [Module 06](../06-identity-aware-access/README.md)
(Pomerium ≈ Cloudflare Access): a request must carry an IdP-issued JWT, checked on every request, and the
backend has no published port.

> **Authorization note.** This is a paper exercise over a *fictional* estate and *public* vulnerability
> reporting — you are not touching any system. The moment you point this rhythm at a real network the
> rule binds: only migrate access for infrastructure you own or are explicitly authorized to manage, aim
> the "is the old path closed?" probes *only* at your own backends, and never decommission a VPN before
> every cohort is provably across with a tested rollback.

---

## Build it — read a little, do a little

### Step 1 — Baseline the estate and name the big-bang trap

**Concept (30 sec):** Flight-card #1 + #2. Before any cutover, you record the starting state (each app
reachable via the flat network, *no identity check*) and you write down — explicitly — what a big-bang
flip would break, so the cohort rhythm has a reason to exist.

**Do it:** in `migration-runbook.md`, write the **baseline** (one line per app: *reachable via VPN/flat
path, no identity required*). Then write the **big-bang trap** you are choosing *not* to do: all four
apps flip at once, VPN off — now `dash.internal` fails, but so might the vendor path to `admin` and the
CI service account, and you can't tell which, can't roll back one slice, and are debugging a company-wide
lockout live.

> **▸ On track if:** your runbook has a baseline row per app *and* a named big-bang trap that describes
> *indistinguishable simultaneous failures + no per-slice rollback* — not just "it's risky."

### Step 2 — Sequence the apps into cohorts, least-risky-first

**Concept (30 sec):** Flight-card #3. A cohort (a migration *wave*) is a small, coherent group of
apps-plus-users you move together. Order by **blast radius and dependency**: lowest stakes and fewest
dependencies first, crown jewels last, and never migrate an app *before* something it depends on in a way
that breaks the dependency over the flat net.

**Do it:** in the runbook, write the cohort order with a one-line *why* per cohort. Watch the trap in the
estate: `dash.internal` reads from `wiki.internal` and pulls `ci-artifacts.internal` over the flat
network — so sequence those dependencies deliberately (and note what the dependency means for the
overlap period). Put `admin.internal` (high sensitivity, external vendor) late.

> **▸ On track if:** your plan sequences **app by app** (or a small coherent wave), least-risky-first,
> with a *why* per cohort, and it does not migrate `dash` in a way that strands its flat-net reads to
> `wiki`/`ci-artifacts` before those are handled — the dependency drives the order, it isn't ignored.

### Step 3 — Define the per-app cutover and its before/after test

**Concept (30 sec):** Flight-card #4. Each cutover is a switch (a DNS record pointing `appN.internal` at
the proxy, or a feature flag) *plus* closing the flat route. The proof is the before/after test asserting
**three** things — and (c) is the one that makes it a real migration.

**Do it:** for one cohort (start with `wiki.internal`), write the exact steps: the **before** capture
(authorized user reaches it via the flat route, 200, *no identity*); the **cutover** (point DNS at the
proxy **and** close the flat route to that backend); and the **after** — the three assertions, written as
checks a teammate could run:
- **(a) No outage:** an authorized user (valid IdP JWT) still gets **200**.
- **(b) Via the proxy:** the request went *through* the proxy — it logged an **allow** and the backend
  sees the proxy-injected identity header; an *unauthenticated* request is now **denied** (non-200).
- **(c) Old flat path closed:** a **direct** request to the backend on the flat network no longer
  connects.

> **▸ On track if:** your cutover step *closes the flat route*, not just adds the proxy, and all three
> assertions are written as concrete checks — with (c) present and phrased as "direct-to-backend no
> longer connects," not implied.

### Step 4 — Attach a per-cohort rollback

**Concept (30 sec):** Flight-card #6. Rollback is cheap *because the VPN is still running* — you never
removed it. Backing a cohort out is "point this cohort's DNS back and re-open its flat route," and it
serves on the old path again in minutes.

**Do it:** for each cohort, write the one-line rollback (the exact reverse of the cutover switch: restore
the flat route, point DNS back) and its trigger ("roll back if any of (a)/(b)/(c) fails, or an app-owner
reports breakage"). Note that a rollback you *specify* but never rehearse is not a rollback — your plan
must include a rehearsal step (flip forward, flip back, flip forward) for at least the first cohort.

> **▸ On track if:** every cohort has a named, reversible rollback tied to a trigger, and the plan
> rehearses at least one — a reader can see how a cohort comes back on the old path in minutes.

### Step 5 — Decommission the VPN last, and prove the surface is zero

**Concept (30 sec):** Flight-card #6, second half. The VPN comes down **only** after the last cohort is
across and every app passes (a)+(b)+(c). Decommission is the org-wide version of the per-cohort flat-path
close — and the one irreversible step.

**Do it:** write the decommission gate as a checklist: *every* app migrated and green on all three
assertions; then close the flat network / stop the VPN; then re-run the full test across **all** apps
(each still 200 via the proxy — no outage from the decommission — and the VPN client can no longer reach
*any* backend directly). State the un-migrated surface is now zero, and this is the last step, taken only
when the gate is fully green.

> **▸ On track if:** decommission is explicitly gated on *all* apps green, is placed **last**, and its
> proof is "all apps still 200 via proxy **and** zero direct flat reach anywhere" — not just "turn the VPN off."

### Step 6 — The legacy 20%: apps that can't speak OIDC

**Concept (30 sec):** Every brownfield estate has apps the happy path can't migrate — a thick client,
a Kerberos/NTLM intranet app, `admin.internal`'s old admin tool, the vendor on a fixed source range.
"Just put OIDC in front of it" fails when the app *can't* consume an OIDC token. An honest migration
names these and gives each a real home instead of leaving them on the flat net forever.

**Do it:** in the runbook, add a **legacy cohort** and route each of its apps to one of two patterns —
and say which and why:

- **Header-injection SSO at the proxy** — the identity-aware proxy authenticates the user (OIDC) and
  passes a *signed* identity header to an app that only understands "trust this header" (the
  `X-Pomerium-Jwt-Assertion` machinery from [Module 06](../06-identity-aware-access/lab.md)). The app
  never learns OIDC; the proxy is the seam. Note the risk you inherit: the app must be reachable *only*
  through the proxy, or the header is forgeable.
- **Shrinking mesh segment** — an app that can't sit behind an HTTP proxy at all (raw TCP, thick client)
  stays on a **default-deny, identity-scoped mesh** ([Module 03](../03-device-trust-posture/lab.md)
  device identity + [Module 07](../07-microsegmentation/lab.md) segmentation) that you *shrink* over
  time, rather than a flat VPN subnet. It's still segmented and identity-gated — just not proxy-fronted.

> **▸ On track if:** your legacy cohort names at least one app per pattern with a one-line *why*, the
> header-injection app is explicitly "reachable only via the proxy," and the mesh-segment app is
> default-deny and identity-scoped — so "we couldn't migrate it" never means "we left it flat."

---

## Prove the control (your finish line)

Assemble `migration-runbook.md` with these sections, then run the one check that proves the plan is
sound:

> *Baseline · Big-bang trap (named, avoided) · Cohort sequence + why · Per-app cutover & before/after
> test · Per-cohort rollback · Decommission gate.*

**The proof:** take your **cohort sequence** and trace one realistic failure through it end-to-end in
writing — "cohort 2 (`dash`) cut over; assertion (c) fails because a direct probe to `dash`'s backend on
the flat net still connects." Show that your plan (i) catches it (the test fails, so the cohort is *not*
declared migrated), (ii) rolls back *only* cohort 2 in minutes while cohorts 1 and 3..N are untouched,
and (iii) does **not** let the VPN decommission proceed. If your runbook can't stop this exact failure at
the cohort boundary, it's a big-bang plan wearing cohort clothing — fix the sequencing or the gate until
it can.

---

## Recall check — close the doc, answer from memory (3 min)

1. The before/after test asserts three things — name all three, and say which one teams most often skip
   and what skipping it leaves open.
2. Why is a per-cohort rollback cheap, and what single condition makes VPN decommission the irreversible
   step you take last?
3. Two reasons to retire the legacy VPN — the access-model one and the appliance one. Which real CVE
   chain made the appliance reason concrete in 2024, and what ZTNA property removes that target?

Missed one? Re-run the step that built it, or pull the [module core idea](README.md#the-core-idea-you-dont-flip-a-switch-you-run-both-move-cohorts-prove-each-then-retire-the-vpn) — then re-answer.

---

## Deliverables

Commit to your portfolio repo:

- **`migration-runbook.md`** — the ordered, strangler-fig runbook: baseline, the named big-bang trap, the
  cohort sequence with *why that order* (least-risky-first, dependencies, coordination), and per cohort
  the cutover mechanism (the DNS record / feature flag), the before/after test, and the decommission
  gate. A portfolio artifact: it shows you can take a *running* VPN estate off the perimeter model
  incrementally without an outage.
- **`cutover-checklist.md`** — the **per-app cutover checklist** a teammate could follow without you: for
  each app, the pre-cutover baseline check, the exact cutover step (switch + close the flat route), the
  three before/after assertions to verify, the rollback command, and the sign-off ("all three green →
  migrated").
- **`rollback-plan.md`** — the per-cohort rollback (the exact reverse switch) with its trigger, and the
  rehearsal step for at least the first cohort.

*Do not commit any credential, key, or real network detail beyond the fictional estate. Lab artifacts
(captures, keys) stay out of commits.*

## Automate & own it

**Required.** Write a short Python or Bash script, `plan-cutover.py` (or `.sh`), that reads a YAML/CSV
**inventory** of apps — each with `name`, `users`, `sensitivity`, `dependencies` — and emits, per app, a
**per-wave cutover checklist**: the app's cohort/wave number (assigned least-risky-first, and never
before an app it depends on), the pre-cutover baseline line, the cutover step, the three before/after
assertions (a/b/c) as a checklist, and the rollback line. Run it against the estate above; the output
*is* your `cutover-checklist.md` starting point.

Have a model draft it from your rubric — then **read every line** and verify two things it will get
wrong: (1) the wave ordering respects dependencies (it must not schedule `dash` in a wave before `wiki`
and `ci-artifacts`, which `dash` reads over the flat net), and (2) assertion **(c)** — "old flat path
closed" — is emitted for *every* app, never dropped. A model asked to "generate a cutover checklist"
tends to produce the "add the proxy" half and omit the "close the flat route" half. A checklist that
sequences by dependency and always includes (c) is the honest one; commit the script alongside the
runbook.

## Definition of done (`vpn-ztna-migration` ✅)

- [ ] The runbook has a per-app **baseline** and a **named big-bang trap** (indistinguishable
  simultaneous failures + no per-slice rollback), the failure the cohort rhythm avoids.
- [ ] Apps are sequenced into cohorts **least-risky-first**, with a *why* per cohort, and the
  `dash` → `wiki`/`ci-artifacts` dependency drives the order (not ignored).
- [ ] Every cohort has a per-app cutover that **closes the flat route** and a before/after test asserting
  all **three** conditions — including (c) the old flat path is closed.
- [ ] Every cohort has a named, reversible **rollback** tied to a trigger, with at least one rehearsed.
- [ ] Decommission is gated on **all** apps green, placed **last**, and proven as "all apps 200 via proxy
  + zero direct flat reach."
- [ ] `plan-cutover.py` emits a dependency-respecting, (c)-always-present per-wave checklist; runbook +
  checklist + rollback plan + script are committed, and you can explain all six flight-card facts cold.

## Connects forward

- **Module 06 — Identity-Aware Access** is the proxy you migrate *to*; this module is "now do it to a
  network that's already running and can't go down." The **no-bypass / trust-only-the-proxy** discipline
  from 06 is exactly what assertion (c) enforces per cohort.
- **Module 07 — Microsegmentation** is the next layer: default-deny *between* the now-migrated services,
  so identity at the front door is paired with segmentation in the interior — the two halves of
  un-flattening the network [Module 01](../01-zero-trust-principles/README.md) indicted.
- The migrated, proxied estate is the system a **red-team-your-own-deployment** module attacks end-to-end
  — including retrying the very flat-path bypass your assertion (c) just closed.

## Marketable proof

> "I plan and run a brownfield VPN → identity-aware (ZTNA) migration without downtime — strangler-fig,
> one cohort at a time: publish each app behind the proxy beside the running VPN, cut each cohort over
> behind a DNS/feature-flag switch, and prove every move with a before/after access test that asserts
> three things — the app is still reachable (no outage), it's now reached *through the proxy* (identity
> enforced per request), and the old flat path is *closed* (no direct-to-backend bypass). Every cohort
> has a tested rollback, the VPN comes down only after the last cohort is provably across, and I can
> explain why a migration is done when the old path is *closed*, not merely when the new one *works* — and
> why big-bang cutovers, and internet-facing VPN concentrators, fail."

## Stretch

- **Cohort by *identity*, not just by app:** cut a cohort over by IdP group (move "engineering" to the
  proxy for `admin.internal` while the vendor stays on the VPN for the same app), so the switch is a
  per-group access policy — the more realistic enterprise rhythm — and write how the two groups take
  different paths to the same service during the overlap.
- **A dependency that breaks the naive order:** in your plan, migrate `dash.internal` *before* `wiki` and
  `ci-artifacts` on purpose, show exactly where the flat-net dependency breaks, then re-sequence —
  proving blast-radius/dependency ordering is the judgment, not a formality.
- **Map the risk to ATT&CK and the appliance CVEs:** tie the migration's *why* to **T1133** (External
  Remote Services) and **T1078** (Valid Accounts), and to the Ivanti/Pulse chain (CVE-2023-46805 +
  CVE-2024-21887) — arguing in one paragraph why removing the concentrator, not patching it, is the
  durable fix.
