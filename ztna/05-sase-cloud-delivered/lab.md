# Lab 05 — Publish a no-inbound-ports app behind a global edge (Cloudflare Access)

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

This lab uses the **Cloudflare Zero Trust free tier** (50 users, no expiring trial) and a local
nginx container. The local environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/05-sase-cloud-delivered
make up        # start the local nginx target container (origin)
make demo      # print setup instructions for the Cloudflare account and tunnel
make down      # stop nginx when done
```

`make up` starts a local nginx container (the private application you will publish through
Cloudflare). `make demo` prints step-by-step tunnel and Access policy setup, since the Cloudflare
account is external and cannot be automated.

**Before the lab steps, sign up for a free Cloudflare Zero Trust account:**
[https://dash.cloudflare.com/sign-up/teams](https://dash.cloudflare.com/sign-up/teams)

You will need: a Cloudflare account (free), a domain you control or a free `*.trycloudflare.com`
hostname (no domain ownership required for the quick-tunnel option), and `cloudflared` installed:

```bash
# macOS
brew install cloudflared

# Linux (Debian/Ubuntu)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Or download a release directly: https://github.com/cloudflare/cloudflared/releases
```

> **Authorization.** This lab publishes a local nginx container that serves no sensitive data,
> through your own personal Cloudflare account, gated to your own email. The red-team steps below
> probe *your own* origin only. Only ever scan or attempt to reach systems you own or have explicit
> written permission to test.

## Scenario

Your architecture decision (Module 04) landed on a cloud-delivered edge. Now ship it: publish an
internal reporting app to the internet with **no inbound ports**, gated by an Access policy that
requires email authentication — then prove the model holds by attacking your own design. The
running, gated service plus the proof of denial *is* the deliverable.

## Build it

1. [ ] **Start the origin.** Run `make up` to start nginx on `localhost:8090`. Verify:
   `curl http://localhost:8090/` returns the status page. This is the "private application" — note
   that right now it listens only on localhost.

2. [ ] **Create a Cloudflare Tunnel.** In the Zero Trust dashboard: **Networks → Tunnels → Create a
   tunnel → Cloudflared**. Name it `ztna-lab`, follow the connector setup, and copy the token. Then
   run the connector locally:
   ```bash
   cloudflared tunnel run --token <your-token>
   ```
   Or the quick-tunnel method (no account needed, but **no Access policy** — use only to see the
   tunnel mechanism, then switch to the named tunnel for the gated build):
   ```bash
   cloudflared tunnel --url http://localhost:8090
   ```
   Confirm the tunnel shows green/connected in the dashboard. Note what just happened: the connector
   dialed *out*. You opened no inbound port.

3. [ ] **Map a public hostname → your origin.** In the tunnel's **Public Hostname** settings, route
   a hostname to `http://localhost:8090`:
   - With a domain in Cloudflare: `ztna-lab.<yourdomain>` → `http://localhost:8090`
   - Without: use the auto-assigned `*.trycloudflare.com` hostname.

4. [ ] **Gate it with an Access policy.** **Access → Applications → Add an application →
   Self-hosted**:
   - Name: `ZTNA Lab App`; Application domain: your hostname from step 3.
   - **Policies → Add a policy**: action **Allow**, name `email-auth`, **Include → Emails → your
     email address**.
   - Save, then browse to the hostname: you should be prompted for an email OTP, and after entering
     it, see the nginx page.

## Red-team your own design

5. [ ] **Verify denial (unauth path).** In a private/incognito window (no session), browse to the
   hostname. You must see the **Cloudflare Access login page, not the app**. Capture this — it is the
   core proof.

6. [ ] **Prove there's no listener.** Confirm the origin is unreachable except through the edge:
   - Locally it serves: `curl http://localhost:8090/` works.
   - The host's port 8090 is not exposed publicly: `netstat -an | grep 8090` (or `ss -ltn`) should
     show it bound to loopback only, not `0.0.0.0`. From a *different* network, an attempt to reach
     your public IP on 8090 (e.g. `nc -vz <your-ip> 8090`) must fail — there is nothing listening.
   - Record this as the "no inbound ports" proof.

7. [ ] **Tighten the policy and re-test the deny path.** Edit the policy and identify, in your
   deliverable, the JSON for each change (use the dashboard's export, or `data/access-policy-example.json`):
   - the field that holds your `include` email rule;
   - how to change it from a single address to an email **domain** (everyone `@`yourdomain);
   - the `require` rule that *also* enforces a WARP device-posture check (an AND on top of identity).
   For each change, state whether it widens or narrows access, and **re-attempt access with a
   credential that should now be denied** — confirm it is.

8. [ ] **Count the attacker's cost (defend the design).** In your deliverable, write a short
   paragraph: compared with a VPN-fronted flat network (one stolen credential + a reachable VPN
   endpoint ≈ the whole network — the Colonial-Pipeline-shaped failure from Module 01), what must an
   attacker now do to reach this app? Name what's *removed* (no exposed port to scan, no fronting
   proxy to fingerprint) and what residual risk *remains* (a stolen valid session, a compromised
   enrolled device, a vendor-side compromise). This is the honest output of red-teaming your design.

9. [ ] **Defend build-vs-buy (the ADR seasoning).** In two or three sentences, state when you'd
   *not* have chosen cloud-delivered for this app — name the concrete condition (data path can't
   traverse a third party / sovereignty / SLA floor / per-seat scale) under which self-hosted ZTNA
   (Pomerium + Headscale from Modules 03/06) would have won instead. The point is a defensible call,
   not a verdict that cloud always wins.

## Success criteria — you're done when

- [ ] The tunnel is connected (green) and the app is reachable through the edge after email auth.
- [ ] An **unauthenticated** request lands on the Access login page, never on the app (captured).
- [ ] You have shown the origin port is bound to loopback and is **not** reachable from another
      network — the "no inbound ports" claim is proven, not asserted.
- [ ] The three policy-JSON changes are identified, and a should-be-denied credential was tested and
      denied.
- [ ] The attacker-cost paragraph and the build-vs-buy defence are written.

*Honor system: there is no grader. These are observable — a connected tunnel, a denial screenshot,
a failed external port probe, a denied test credential. Check your own work honestly against them.*

## Deliverables

`cloudflare-zt-deployment.md` containing:
- proof the tunnel is connected and the Access policy is active (screenshot or `cloudflared` log);
- the unauthenticated-denial capture **and** the no-listener proof (the external probe result);
- the three Access-policy JSON changes (domain email rule, WARP `require`, posture check);
- the attacker-cost paragraph and the build-vs-buy defence.

Do **not** commit your Cloudflare tunnel token or any account credentials.

## Automate & own it

**Required.** Write a Python script (`verify-access.py`) that turns "is this request really
authenticated?" into a repeatable check:
1. Takes a URL (your public hostname) and a Cloudflare Access JWT as arguments.
2. Fetches Cloudflare's signing keys (the team's JWKS) and verifies the JWT **signature**.
3. Verifies the **`aud`** claim matches your application's expected audience.
4. Verifies expiry, and prints the identity claims (`email`, `iat`, `exp`).
5. Prints PASS only if signature **and** audience **and** expiry all hold; FAIL otherwise.

Cloudflare issues a short-lived JWT on successful auth and passes it as a header to your origin;
log nginx request headers to capture one. Have a model draft the validator, then **review the `aud`
check specifically** — a script that validates the signature but skips the audience is fooled by a
perfectly valid token minted for a *different* Cloudflare application. AI drafts → you verify the
audience logic → you own the check.

## AI acceleration

Ask a model to draft the Access application JSON from a plain-English policy description, then
**diff every field against `data/access-policy-example.json` and the current Cloudflare docs.**
Recurring model mistakes: deprecated field names the dashboard silently ignores, and `include`
where `require` is needed (OR vs AND — the difference between "any of these" and "all of these").
Always close the loop the same way: test the policy with a credential that *should fail*, not just
one that should succeed.

## Connects forward

You've now shipped the cloud-delivered half of the architecture you decided in Module 04. Module 06
builds the self-hosted counterpart (a Pomerium identity-aware proxy you run yourself) — the same
deny-path discipline, on the other side of the build-vs-buy call you just defended. The Phase-3
red-team module generalises step 5–6 here into attacking your *whole* deployment, including forging
proxy identity headers and bypassing the proxy straight to the backend.

## Marketable proof

> "I published a private application to the internet with zero inbound ports via a Cloudflare Zero
> Trust tunnel, gated it with an Access policy, and proved — by external port probe and an
> unauthenticated request — that it's only reachable after edge authentication. I can defend the
> cloud-delivered-vs-self-hosted call on ops-burden-vs-control grounds and quantify the
> blast-radius reduction versus a VPN model."

## Stretch

- Add a second Access policy requiring **WARP enrollment** (device posture). Install the WARP
  client, enroll your device, and verify the policy now gates on device posture *in addition to*
  email — confirm an un-enrolled device is denied even with a valid email.
- Configure **Cloudflare Gateway** DNS filtering: add a DNS policy blocking the managed "Malware"
  category and verify it blocks a test lookup (e.g. `malware-traffic-analysis.net` — safe to query;
  it's a research site, not malware) — the SWG slice of the broader SASE stack.
