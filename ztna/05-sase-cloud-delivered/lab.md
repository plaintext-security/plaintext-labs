# Lab 05 — SASE & Cloud-Delivered Zero Trust: Cloudflare Access

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This lab uses the **Cloudflare Zero Trust free tier** (50 users, no trial expiry) and a local
nginx container. The local environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/05-sase-cloud-delivered
make up        # start the local nginx target container
make demo      # print setup instructions for the Cloudflare account and tunnel
make down      # stop nginx when done
```

`make up` starts a local nginx container (the private application you will publish through
Cloudflare). `make demo` prints step-by-step tunnel and Access policy setup instructions, since
the Cloudflare account is external and cannot be automated.

**Before starting the lab steps, sign up for a free Cloudflare Zero Trust account:**
[https://dash.cloudflare.com/sign-up/teams](https://dash.cloudflare.com/sign-up/teams)

You will need: a Cloudflare account (free), a domain you control or a free `*.trycloudflare.com`
hostname (no domain ownership required for the quick tunnel option), and `cloudflared` installed
on your machine.

**Install `cloudflared`:**
```bash
# macOS
brew install cloudflared

# Linux (Debian/Ubuntu)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Or download directly: https://github.com/cloudflare/cloudflared/releases
```

> This lab accesses Cloudflare's public infrastructure via your personal account. You are
> publishing a local nginx container that serves no sensitive data. The Access policy you configure
> gates access to your own email address only.

## Scenario

Meridian's CISO approved the cloud-edge architecture recommendation from Lab 04. The first 90-day
deliverable is publishing the internal reporting application through Cloudflare Zero Trust — no
inbound ports, Access policy requiring corporate email authentication. You'll prove the model works
by publishing your local nginx container as a private application, configuring an Access policy,
and demonstrating that the application is unreachable without authenticating through Cloudflare's
edge.

## Do

1. [ ] **Start the local application.** Run `make up` to start the nginx container on port 8090
   locally. Verify it is running: `curl http://localhost:8090/` — you should see the Meridian
   status page. This is the "private application" you will publish.

2. [ ] **Create a Cloudflare Tunnel.** In the Cloudflare Zero Trust dashboard:
   - Navigate to **Networks → Tunnels → Create a tunnel**
   - Choose **Cloudflared**, name the tunnel `meridian-lab`
   - Follow the connector setup; copy the token it gives you
   
   Then run `cloudflared` locally pointing at your nginx:
   ```bash
   cloudflared tunnel run --token <your-token>
   ```
   Or use the quick-tunnel method (no account required, but no Access policy):
   ```bash
   cloudflared tunnel --url http://localhost:8090
   ```
   Confirm the tunnel is connected in the dashboard (green status).

3. [ ] **Configure a public hostname.** In the tunnel settings, add a public hostname:
   - If you have a domain in Cloudflare: `meridian-lab.<yourdomain.com>` → `http://localhost:8090`
   - If not: use the auto-assigned `*.trycloudflare.com` hostname from the quick tunnel

4. [ ] **Create an Access policy.** In the Zero Trust dashboard:
   - Navigate to **Access → Applications → Add an application → Self-hosted**
   - Application name: `Meridian Lab App`
   - Application domain: your hostname from step 3
   - Under **Policies → Add a policy**: Allow, name it `email-auth`
     - Include rule: **Emails** → your email address
   - Save and test: browse to your hostname. You should be prompted for email verification.
   
   Authenticate with your email. After verification, you should see the nginx page.

5. [ ] **Verify denial.** In a private/incognito window (unauthenticated), browse to the hostname.
   You should see the Cloudflare Access login page, not the nginx page. Also confirm: the nginx
   container on port 8090 is reachable locally (`curl http://localhost:8090/`) but the same
   content is not reachable from the public internet on that port (try directly from a different
   network with `nc -v <your-ip> 8090`, or use `netstat -an | grep 8090` to verify the port is
   only listening on localhost). The application is only accessible via the tunnel.

6. [ ] **Inspect the Access policy JSON.** In the Zero Trust dashboard, the Access application
   has an export option (or review `data/access-policy-example.json` for a representative
   example). Identify:
   - Which field in the JSON corresponds to the `include` rule you configured?
   - What would you change to require that the user's email domain is `@meridian.com` rather
     than a specific address?
   - What `require` rule would you add to also enforce that the WARP device posture check passes?
   Write these changes in your deliverable.

7. [ ] **Relate to Meridian's SWIFT gateway.** In your deliverable, write a paragraph: if Meridian
   deployed the SWIFT gateway behind a Cloudflare Tunnel with an Access policy requiring (a) email
   matching `@meridian.com`, (b) WARP device enrollment, and (c) CrowdStrike ZTA score ≥ 70, what
   does an attacker now need to do compared to the current model (Domain Admin + RDP)? Quantify the
   blast-radius reduction.

## Success criteria — you're done when

- [ ] The tunnel is running and green in the Cloudflare dashboard.
- [ ] Browsing to the public hostname prompts for email verification before showing the nginx page.
- [ ] You have confirmed that port 8090 on the host is not externally reachable.
- [ ] The policy JSON analysis is written (three specific changes identified).
- [ ] The SWIFT gateway paragraph is in the deliverable.

## Deliverables

`cloudflare-zt-analysis.md` containing:
- Screenshot or log output showing the tunnel connected and the Access policy active
- The three Access policy JSON changes (domain-based email rule, WARP requirement, posture check)
- The SWIFT gateway blast-radius paragraph

Do not commit your Cloudflare tunnel token or any account credentials.

## Automate & own it

**Required.** Write a Python script (`verify-access.py`) that:
1. Takes a URL (your public hostname) and a Cloudflare Access JWT token as arguments
2. Checks that the JWT's `aud` matches the expected application audience
3. Validates the JWT's expiry and prints the identity claims (email, `iat`, `exp`)
4. Prints PASS if the token is valid for the expected audience, FAIL otherwise

Cloudflare issues a short-lived JWT on successful authentication that it passes as a header to
your origin; you can inspect it by logging request headers from nginx. Have a model draft the
validation script; **review the `aud` validation logic** — a script that validates the signature
but not the audience can be fooled by a valid token from a different Cloudflare application.

## AI acceleration

Ask a model to draft the Cloudflare Access application JSON config from a description of the
policy. Then **compare every field against `data/access-policy-example.json`** and the Cloudflare
documentation. Common model mistakes: using deprecated field names (`allow_authenticate_via_warp`
vs. the current `require_gateway_device_posture`), and generating a policy with `include` where
`require` is needed (OR vs. AND). Test your policy by attempting access with a credential that
should fail — not just one that should succeed.

## Connects forward

This is the final module in the ZTNA track. The patterns you've built here — ZT gap analysis,
identity broker, device posture enforcement, architecture decision, and SASE deployment — are the
complete ZT lifecycle: assess, design, and implement. The Meridian scenario threads through all
five modules; the gap analysis from Lab 01 is closed by the controls from Labs 02–05.

## Marketable proof

> "I have deployed a Cloudflare Zero Trust tunnel, published a private application with an Access
> policy requiring identity verification and no inbound ports, and can articulate the blast-radius
> reduction vs. a VPN model — the hands-on proof of SASE/ZTNA deployment skills."

## Stretch

- Add a second Access policy that requires WARP enrollment (device posture check). Install the
  Cloudflare WARP client, enroll your device, and verify that the policy gates on device enrollment
  in addition to email identity.
- Configure Cloudflare Gateway DNS filtering: add a DNS policy that blocks known malware C2
  domains (use the Cloudflare-managed "Malware" category blocklist) and verify it blocks a test
  domain like `malware-traffic-analysis.net` (safe to query; the site is a security research
  resource, not malware itself).
