# Lab 05 — TLS Deep Dive

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/05-tls-deep-dive
make up        # build nginx with weak config + testssl.sh container
make demo      # scan the weak config, show findings, switch to strong config, rescan
make shell     # drop into the testssl container
make down      # stop when done
```

> Everything runs locally. The nginx server is on the Docker bridge network — no external
> connections needed.

## Scenario

Meridian Financial's external security assessment found their internal API gateway is running
nginx with TLS 1.0 enabled and several weak cipher suites. You have been asked to: reproduce
the assessment findings, understand each one, apply the Mozilla "modern" TLS profile, and
rescan to confirm the findings are resolved.

## Do

1. [ ] `make demo` — watch testssl.sh scan the weak nginx configuration. Record: which TLS
   versions are supported, which cipher suites are flagged, and any certificate findings.

2. [ ] `make shell` and rescan the weak nginx yourself with `testssl.sh`, filtering to the
   serious findings. For each HIGH or CRITICAL: which cipher suite or setting causes it, and
   which property does it undermine (forward secrecy, authentication, confidentiality)?

3. [ ] Open the weak nginx config (`data/nginx-weak.conf`) and map each scanner finding back to
   the specific directive that produces it. Which `ssl_protocols` / `ssl_ciphers` lines are the
   root causes?

4. [ ] Apply the Mozilla "modern" profile. Use the Mozilla SSL Configuration Generator to
   derive the correct `ssl_protocols`, `ssl_ciphers`, `ssl_prefer_server_ciphers`, and HSTS
   directives, write them into `data/nginx-strong.conf`, reload nginx with the strong config
   (`make reload-strong`), and rescan. How many findings remain?

5. [ ] Inspect the negotiated handshake directly with `openssl s_client` against the strong
   server. What protocol and cipher suite were negotiated, which key-exchange algorithm is in
   use, and is it forward-secret?

6. [ ] Write `tls-audit-report.md`: a table with finding name, severity, affected property,
   weak config directive, and strong config fix for the top five findings.

## Success criteria — you're done when

- [ ] You identified the weak config's HIGH/CRITICAL findings and their root causes.
- [ ] You applied the Mozilla modern profile and confirmed the findings are resolved.
- [ ] You used `openssl s_client` to inspect the negotiated cipher and protocol.
- [ ] You produced a `tls-audit-report.md` with finding → root cause → fix.

## Deliverables

`tls-audit-report.md` — your five-finding table. Commit it.

## Automate & own it

**Required.** Write a shell script `tls-check.sh` that runs `testssl.sh` against a host:port,
parses the output for HIGH and CRITICAL severity findings, and exits non-zero if any are
found. Wire it into a GitHub Actions workflow that runs the check against a test endpoint on
every PR. Have an AI draft the grep/awk parsing; you verify the exit code is non-zero when
HIGH findings are present.

## AI acceleration

Paste the testssl.sh output line for a specific HIGH finding into an AI and ask: "What is
this TLS finding, what can an attacker do if this is present, and what is the nginx
configuration change that fixes it?" Verify the nginx fix against the Mozilla SSL
Configuration Generator output for the "modern" profile.

## Connects forward

The cipher suite knowledge from this module is the foundation for module 06 (PKI & Certificate
Management) — a properly configured CA needs to issue certificates with strong signature
algorithms — and module 10 (Auditing Applied-Crypto Failures), where you audit a matrix of
TLS configurations and score the delta.

## Marketable proof

> "I ran testssl.sh against a weak TLS configuration, identified HIGH/CRITICAL findings,
> applied the Mozilla modern TLS profile, and confirmed all findings were resolved — producing
> an audit evidence report."

## Stretch

- Use Wireshark (or `tcpdump + tshark`) to capture the TLS 1.3 handshake and decode the
  ClientHello. Identify: supported groups, signature algorithms, and ALPN extensions. What
  does the ServerHello contain?
- Research HSTS preloading: what is `includeSubDomains` and `preload` in the
  `Strict-Transport-Security` header, what is the preload list, and what is the risk of
  submitting a domain before you're ready?
