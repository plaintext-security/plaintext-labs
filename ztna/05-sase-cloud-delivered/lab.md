# Lab 05 — Publish a no-inbound-ports app behind a global edge (Cloudflare Access)

> **Hands-on lab.** Environment: `plaintext-labs/ztna/05-sase-cloud-delivered`.
> Objective: **publish a private app through a SASE tunnel with zero inbound ports, gate it at the
> edge, and prove an unauthenticated request can't reach it.**
> Target: **~90 min**, one finish line. This lab is **part local (a `make`-managed nginx origin), part
> external** (your own free Cloudflare Zero Trust account + `cloudflared` on the host) — be honest with
> yourself about which half you're in at each step.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The origin opens NO inbound port.** `cloudflared` dials *out* to the edge. | The whole security model: an IP scan of your server finds nothing to hit. |
| 2 | **The edge evaluates the Access policy *before* forwarding.** | No policy match → the request never reaches the app, only the login page. |
| 3 | **`include` is OR; `require` is AND.** | A policy with only an `include` and no `require` is valid *and wide open*. |
| 4 | **Proving denial is the deliverable**, not the happy path. | "It let me in" proves nothing; "it turned away an unauth request" is the proof. |
| 5 | **Prove "no listener" by trying to find one.** | Loopback-only bind + a failed external port probe = the claim is proven, not asserted. |
| 6 | **Build-vs-buy is ops-burden vs control** — defend the call. | Cloud-delivered isn't "always right"; naming when self-hosted wins is the marketable skill. |

*(If you can explain all six cold at the end — especially #1 and #4 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [tunnel mechanic](README.md#the-tunnel-is-the-whole-trick) and the
> [build-vs-buy table](README.md#the-judgment-cloud-delivered-vs-self-hosted).

---

## Warm-up — answer before you touch the dashboard (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Your app is published to the whole internet, yet an attacker who port-scans your server's public IP
   finds nothing on it. In one sentence, **where is the socket** that serves traffic — and why isn't it
   on your box?
2. You write a policy with `include: any @company.com email` and no `require` clause. Who exactly can
   get in — and which flight-card fact says that's a bug, not a config you can leave?

---

## Setup

The **local origin** lives in the companion `plaintext-labs` repo; the **edge and account are
external** (your own free Cloudflare Zero Trust tenant). `make demo` prints the external steps because
the Cloudflare side can't be automated.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/05-sase-cloud-delivered
make up        # LOCAL: start the nginx origin on localhost:8090
make demo      # prints the EXTERNAL Cloudflare tunnel + Access setup steps
make down      # stop nginx when done
```

**External prerequisites (do these once, on your own account):**

```bash
# 1. Sign up for Cloudflare Zero Trust (free, 50 users, no expiry):
#    https://dash.cloudflare.com/sign-up/teams
# 2. Install cloudflared:
brew install cloudflared                       # macOS
# Linux: https://github.com/cloudflare/cloudflared/releases
```

> **▸ On track if:** `make up` reports nginx at `http://localhost:8090`, `curl http://localhost:8090/`
> returns the Corp app page, and `make demo` prints the three-step (quick tunnel → named tunnel +
> Access → verify denial) brief. The seed you reason *about* is **`data/access-policy-example.json`**
> — four policy tiers, email-only up to CrowdStrike posture.

> **Authorization note.** You publish a *local* nginx page that serves no sensitive data, through
> *your own* free Cloudflare account, gated to *your own* email. Every red-team step probes *your own*
> origin only. Only ever scan or attempt to reach systems you own or have explicit written permission
> to test.

---

## Build it — read a little, do a little

### Step 1 — Start the origin and note what's *not* listening

**Concept (30 sec):** Flight-card #1. Right now nginx binds `localhost:8090` — private, on your box.
The point of the whole lab is that it *stays* that private after it's published to the planet.

**Do it:** `make up`, then `curl http://localhost:8090/`. Confirm the page renders. Run `ss -ltn` (or
`netstat -an | grep 8090`) and note it's bound to loopback — you'll use this exact fact as evidence in
Step 5.

> **▸ On track if:** the curl returns the Corp app HTML and the port shows bound to `127.0.0.1` /
> loopback — not `0.0.0.0`. You have a private app and, so far, no way to reach it from outside.

### Step 2 — Dial the tunnel OUT (the inversion)

**Concept (30 sec):** Flight-card #1 again — this is the move that deletes the inbound appliance from
Module 05's case study. `cloudflared` opens an *outbound* connection to the edge; you never open a port.

**Do it (external):** the fastest proof is the quick tunnel, which needs no account:
```bash
cloudflared tunnel --url http://localhost:8090
```
It prints a `*.trycloudflare.com` URL — browse to it and you'll see the Corp app. **But note the
caveat:** a quick tunnel has *no Access policy* — it's open to the world. Use it only to witness the
mechanism, then switch to a **named tunnel** (`cloudflared tunnel login` → `create` → `route dns` →
`run`, per `make demo`) for the gated build.

> **▸ On track if:** the tunnel shows green/connected and the app is reachable through the edge URL —
> and you opened **no** inbound firewall rule to make that happen. Sit with that for a second: the
> app is public and your box has no listening public port.

### Step 3 — Gate it with an Access policy (identity at the edge)

**Concept (30 sec):** Flight-card #2. Publishing ≠ protecting. The edge only forwards a request *after*
your policy passes; an unmatched request never touches the origin.

**Do it (external):** in the Zero Trust dashboard → **Access → Applications → Add application →
Self-hosted**. Set the domain to your tunnel hostname; add a policy **Allow**, `include → Emails → your
own address`. Save, then browse: you should get an email OTP prompt, and only after it, the app.

> **▸ On track if:** browsing the hostname now shows the **Cloudflare Access login**, and the app
> appears only after you complete email auth. If the app loads with no prompt, your named tunnel
> hostname isn't the one the application is bound to — recheck the domain field.

### Step 4 — Read the policy tiers (OR vs AND, on paper)

**Concept (30 sec):** Flight-card #3. `include` is OR (any one match admits you); `require` is AND
(every rule must hold). This is the single field where "valid" and "wide open" coincide.

**Do it:** open **`data/access-policy-example.json`** and walk the four tiers: `email-auth-basic`
(one address) → `corp-email-domain` (any `@corp.com` — an OR widening) → `corp-email-with-warp` (domain
**AND** WARP enrolled — a `require`) → `corp-email-with-posture-score` (domain **AND** CrowdStrike ZTA
score ≥ 70). For each, say in one line whether it *widens* or *narrows* access and whether the change
lives in `include` or `require`.

> **▸ On track if:** you can point at the exact JSON field that turns your single-email rule into a
> domain rule (it's under `include`), and the exact field that adds the device-posture AND (it's under
> `require`) — and you can state that the tier with only `include` and empty `require` is the wide-open
> one from flight-card #3.

### Step 5 — Prove there's no listener (the core red-team check)

**Concept (30 sec):** Flight-card #5. The security *is* "no inbound socket," so you prove it by failing
to find one — from a network that isn't your loopback.

**Do it (probe your OWN origin only):**
- Local still serves: `curl http://localhost:8090/` works.
- Loopback bind confirmed from Step 1 (`ss -ltn` → `127.0.0.1:8090`, not `0.0.0.0`).
- From *off* your host — a phone on cellular, or an external TCP-check service like `check-host.net`
  against your public IP on port 8090 — the probe must **fail** (nothing listening). Capture the failure.

> **▸ On track if:** you have a *failed* external probe of port 8090 alongside a *working* localhost
> curl. That pair is the "no inbound ports" proof — asserted becomes demonstrated. (This is the
> authorization line: you're probing your own IP and nothing else.)

### Step 6 — Prove denial, then defend the design

**Concept (30 sec):** Flight-card #4 + #6. The unauth-denial capture is the deliverable's spine; the
build-vs-buy defence is what makes you an architect and not a button-pusher.

**Do it:**
- In a private/incognito window (no session), browse the hostname → you must land on the **Access login
  page, not the app**. Screenshot it. This is the core proof.
- Edit the policy to add a `require` (WARP posture, per tier 3 of the JSON), then **re-attempt with a
  credential that should now be denied** — an un-enrolled device or a non-included email — and confirm
  it *is* denied.
- Write the **attacker-cost** paragraph: versus a VPN-fronted flat network (Colonial: one stolen
  credential + a reachable endpoint ≈ the whole network) — and versus the *un-credentialed*
  Ivanti/Citrix/Pulse appliance breaches — what's *removed* (no exposed port, no fronting proxy to
  fingerprint) and what *residual* remains (stolen valid session, compromised enrolled device,
  vendor-side compromise).
- Write the **build-vs-buy defence**: name the one concrete condition (data path can't traverse a third
  party / sovereignty / SLA floor / per-seat scale) under which you'd have chosen self-hosted instead.

> **▸ On track if:** you have (a) the incognito login-page screenshot, (b) a documented denied test
> credential *after* tightening the policy, (c) an attacker-cost paragraph that names both what's
> removed and what residual remains, and (d) a build-vs-buy defence that names a real condition — not
> "cloud always wins."

---

## Prove the control (your finish line)

Assemble `cloudflare-zt-deployment.md`, then confirm the one thing the whole model rests on:

> *Deployment proof (tunnel connected + Access active) · Unauthenticated-denial capture ·
> No-listener proof (failed external probe) · The three policy-JSON changes (domain rule, WARP
> `require`, posture score) · Attacker-cost paragraph · Build-vs-buy defence.*

**The proof:** an **unauthenticated** browser lands on the Access login page **and** an external probe
of your origin's port 8090 **fails** — published to the internet, yet with no reachable listener and no
way past the edge without auth. *If either the unauth request reaches the app, or the external probe
succeeds, the design isn't holding — fix it before you write it up.*

---

## Recall check — close the doc, answer from memory (3 min)

1. The app is public but its port scans as closed. Where is the socket, and what does `cloudflared`
   dial to make that true?
2. `include` vs `require` — which is OR, which is AND, and which one, left alone, silently opens the door?
3. Name two things the SASE model *removes* from the attacker's job, and two residual risks it does
   **not** remove.

Missed one? Re-run the step that built it, or pull the [tunnel mechanic](README.md#the-tunnel-is-the-whole-trick) — then re-answer.

---

## Deliverables

- **`cloudflare-zt-deployment.md`** — the portfolio artifact, containing:
  - proof the tunnel is connected and the Access policy is active (screenshot or `cloudflared` log);
  - the unauthenticated-denial capture **and** the no-listener proof (the failed external probe);
  - the three Access-policy JSON changes (domain email rule, WARP `require`, posture check);
  - the attacker-cost paragraph and the build-vs-buy defence.

*Do **not** commit your Cloudflare tunnel token or any account credentials. Lab artifacts (tokens,
session cookies, JWTs) stay out of the commit.*

## Automate & own it

**Required.** Turn "is this request *really* authenticated?" into a repeatable check. Write
`verify-access.py` that:

1. Takes a URL (your public hostname) and a Cloudflare Access JWT as arguments.
2. Fetches your team's JWKS (signing keys) and verifies the JWT **signature**.
3. Verifies the **`aud`** claim matches your application's expected audience.
4. Verifies expiry, and prints the identity claims (`email`, `iat`, `exp`).
5. Prints **PASS** only if signature **and** audience **and** expiry all hold; **FAIL** otherwise.

Cloudflare mints a short-lived JWT on successful auth and passes it to your origin as a header — the
lab's `data/nginx.conf` is already set up to surface the `Cf-Access-Jwt-Assertion` header so you can
grab one. Have a model draft the validator, then **review the `aud` check specifically**: a script that
verifies the *signature* but skips the *audience* is fooled by a perfectly valid token minted for a
*different* Cloudflare application. AI drafts → you verify the audience logic → you own the check. Commit
`verify-access.py` alongside `cloudflare-zt-deployment.md`.

## Definition of done (`sase-cloud-delivered` ✅)

- [ ] The tunnel is connected (green) and the app is reachable through the edge **only after** email auth.
- [ ] An **unauthenticated** request lands on the Access login page, never the app — captured.
- [ ] The origin port is shown bound to loopback **and** unreachable from another network (failed external probe) — the "no inbound ports" claim is proven, not asserted.
- [ ] The three policy-JSON changes are identified, and a should-be-denied credential was tested and denied.
- [ ] The attacker-cost paragraph and the build-vs-buy defence are written.
- [ ] `verify-access.py` verifies signature **and** `aud` **and** expiry; you can explain all six flight-card facts cold.

## Connects forward

- **Module 04 — ZTNA Architectures** is where you *decided* on a cloud-delivered edge; this lab shipped it.
- **Module 06 — Identity-Aware Access** builds the self-hosted counterpart (a Pomerium proxy you run
  yourself) — the same deny-path discipline, on the other side of the build-vs-buy call you just defended.
- **Module 11 — Red-team the ZT Deployment** generalises Steps 5–6 into attacking your *whole* stack:
  forging proxy identity headers, bypassing the edge straight to a mis-bound backend.

## Marketable proof

> "I published a private application to the internet with zero inbound ports via a Cloudflare Zero Trust
> tunnel, gated it with an Access policy, and proved — by external port probe and an unauthenticated
> request — that it's reachable only after edge authentication. I can explain why this class of design
> is structurally immune to the inbound-VPN-appliance breaches (Ivanti, CitrixBleed, Pulse), defend the
> cloud-delivered-vs-self-hosted call on ops-burden-vs-control grounds, and quantify the blast-radius
> reduction versus a VPN model."

## Stretch

- Add a second Access policy requiring **WARP enrollment** (device posture). Install the WARP client,
  enroll your device, and verify the policy now gates on posture *in addition to* email — confirm an
  un-enrolled device is denied even with a valid email. (This is the SASE **device** slice.)
- Configure **Cloudflare Gateway** DNS filtering: add a DNS policy blocking the managed "Malware"
  category and verify it blocks a test lookup — the **SWG** slice of the broader SASE stack you read
  about in the module.
- **Third-party / contractor access (the lab you already built, reframed).** The Access policy you stood
  up *is* clientless third-party access — no VPN, no agent on their laptop. Add a second app/route and a
  policy that admits an **external auditor** by email for a **time-boxed** window (Access session
  duration / purpose-justification), gated on identity only — *not* device posture, since you don't
  manage their machine. Then prove the boundary: from that auditor identity you reach the audit app but
  are **denied** the admin route. This is one of the most common enterprise ZTNA purchase drivers —
  granting outsiders scoped access with **no network foothold**.

---

### Stretch+ — Bring your own enterprise IdP (Okta), then go passwordless

*Bigger, and unapologetically not-OSS — this is the **marketable** one. It needs a free Okta org on
top of your Cloudflare tenant, so it's strictly opt-in; the required lab above stays 100% free and
local. Everything here is **your own** org and **your own** app — the same authorization rule holds.*

> **⚠ Status: doc-verified, not yet run end-to-end.** These steps are written against the current
> Okta and Cloudflare Zero Trust docs but haven't been walked through a live tenant, so dashboard
> navigation and field labels may have drifted. Treat it as a guided path, not a validated one — and
> if you run it, note any correction (a moved menu, a renamed field) and send a PR. The rest of this
> lab (the required, non-stretch part) **is** validated.

**Why bother.** The main lab gated on an *email you typed into Cloudflare*. Real enterprises gate on
**group membership in the company IdP**. This swaps Cloudflare's built-in email-OTP for **Okta as the
OIDC identity provider**, and moves the access decision onto an **Okta group** — the exact federation
seam [Module 02](../02-identity-control-plane/lab.md) had you design on paper (its Step 4c: Okta
`groups` → your app's authz, the Golden SAML / **T1606.002** seam). Here you *run* it.

**A — Okta as the OIDC IdP behind the edge.**
- Create a free **Okta Integrator** org — <https://developer.okta.com/signup> (no card, no expiry).
- In Okta: **Applications → Create App Integration → OIDC → Web Application**. Set the redirect URI to
  `https://<your-team>.cloudflareaccess.com/cdn-cgi/access/callback`, and set the **Groups claim
  filter** to *Matches regex* `.*` so group membership rides in the token. Copy the **Client ID**,
  **Client secret**, and your **Okta domain**.
- Create an Okta group (e.g. `corp-eng`) and put **only one** of your two test users in it.
- In Cloudflare: **Zero Trust → Integrations → Identity providers** (older dashboards:
  *Settings → Authentication → Login methods*) → **Add new → Okta**. Paste **App ID** (the Client ID),
  **Client secret**, and **Okta account URL**; test the connection.
- Re-point your Access application's policy: replace `include → Emails → your address` with
  `include → Okta groups → corp-eng`.

> **▸ On track if:** browsing the hostname now bounces you to **Okta's** login (not Cloudflare's email
> OTP), and after Okta auth the app loads — *only* for the user in `corp-eng`. **The proof is the
> denial:** log in as the user you left **out** of the group → Okta authenticates them fine, but
> **Cloudflare denies at the policy**. Identity ≠ authorization; the group is the decision. Screenshot
> that denial — it's the stretch's spine, same as the unauth denial was the main lab's.

**B — Add MFA (Google Authenticator / TOTP).** In Okta → **Security → Authenticators**, add **Google
Authenticator** and require it in the app's sign-on policy. Log in again: Okta now demands the 6-digit
code before it will assert your identity to Cloudflare. **The lesson:** the *factor* decision moved to
the **IdP** — **Cloudflare's config didn't change at all.** The edge just consumes whatever assurance
Okta vouches for.

**C — Go fully passwordless (passkey).** *Additional.* In the same authenticator settings, enable
**WebAuthn** (passkey) / **Okta FastPass** and make it the primary factor. Re-login with a platform
passkey — no shared secret ever crosses the wire. One line in your write-up on why phishing-resistant
passwordless is the endgame the whole ZT identity story walks toward.

**The reused insight — no new script needed.** Your `verify-access.py` from *Automate & own it* **still
passes unchanged.** Why? Cloudflare mints its *own* Access JWT after brokering Okta, so your validator
never sees an Okta token — it checks the same Cloudflare `aud` + signature as before. That's the
architect's point worth writing down: **the edge normalizes identity**, so the IdP behind it is
swappable without touching the app or its token checks.

**Deliverable (stretch).** A short **`okta-federation.md`** addendum: the Okta-brokered login
screenshot, the **group-based denial** capture (the user left out of `corp-eng`), and 2–3 sentences
tying it to the Module 02 seam — *the Okta-group → Access-policy map is where authorization actually
lives; whoever controls Okta group membership controls your app.* Don't commit the Okta client secret
or any JWT.

> **Marketable proof (if you did this stretch):** "I integrated **Okta** as the enterprise identity
> provider into a Zero Trust edge over OIDC, gated application access on **Okta group membership** (not
> just email), and enforced **phishing-resistant passwordless** login — and I can explain why the
> edge's own Access token means the IdP behind it is swappable without changing the protected app."
