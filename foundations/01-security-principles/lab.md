# Lab 01 — The Equifax Autopsy: Map Every Failure to a First Principle

*Variant D · concept autopsy. [← Back to the module concept](README.md)*

## Setup
This lab has **no exploitation and no Docker** — the skill is *judgment*, not tooling. It ships a small
helper in the companion [`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo
that prints the autopsy template and a tiny cert-expiry checker you'll make your own.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/foundations/01-security-principles
make demo       # print the principle-autopsy template
```

Python 3 only. You'll also want the [GAO report](https://www.gao.gov/products/gao-18-559) from the
module open as your evidence file.

> Only test systems you own or have explicit written permission to test. This lab attacks nothing — it
> reasons about a *published* breach from public reports. The cert-checker script you write is run only
> against hosts you own (or the public example given).

## Scenario
You're the analyst assigned to write the one-page **principle autopsy** of the Equifax breach — the
artifact that turns "they got hacked" into "here is *exactly* which principle failed, in what order, and
the one control that would have broken the chain there." A CISO will read your bottom line. The headline
("they didn't patch") is the trap; your job is to show it was a *chain*.

Each step runs the same rhythm: **Predict** (commit before you look) → **Read** (find it in the GAO
report) → **Map** (name the principle) → **Record** (one row in the autopsy).

## Do

1. [ ] **Re-commit your prediction.** Before reading further, write your one-line answer to the README's
   question — *"what was the one thing that failed?"* — at the top of your autopsy. You'll grade it at
   the end. Owning a wrong guess is the lesson.

2. [ ] **Hop 1 — the entry (the unpatched Struts hole).**
   **Predict:** which CIA property is first put at risk when an attacker can run commands on your server?
   **Read:** find **CVE-2017-5638** and the patch timeline in the GAO report (a fix existed before the
   breach). **Map:** this is a missing/late control — patch management. **Record:** owner = the entry;
   property at risk = confidentiality; breaking change = apply the available patch promptly.

3. [ ] **Hop 2 — the spread (the flat internal network).**
   **Predict:** one server is compromised. Should the attacker now be able to reach *every* database?
   **Read:** find how attackers moved internally and why segmentation didn't stop them.
   **Map:** name the principle that was **missing** — defense in depth *and* least privilege (the server
   could reach data it had no business touching). **Record:** principle = defense in depth / least
   privilege; breaking change = network segmentation + scope the server's access.

4. [ ] **Hop 3 — the blind spot (the expired certificate).**
   **Predict:** the data leaving the network — why did nobody notice for ~76 days?
   **Read:** find the expired certificate on the traffic-inspection device and how long it was blind.
   **Map:** this is the subtle one. Tie it to **two** ideas: **Accounting** (the logging/monitoring leg
   of AAA) and the **availability of detection** (the defense itself was unusable). **Record:**
   principle = AAA/accounting + availability-of-monitoring; breaking change = monitor the monitors
   (alert on expired certs / dead inspection).

5. [ ] **Render the autopsy.** Write the one-page memo: a row per hop (the failure · the principle ·
   the one breaking change), then a two-sentence bottom line answering *"was there one thing that
   failed?"* — **no: at least three principles failed in series, and each was supposed to catch the
   last.** Score your step-1 prediction against this.

## Success criteria — you're done when
- [ ] `principle-autopsy.md` maps each of the three hops to a named principle (CIA / AAA / defense in
  depth / least privilege) and gives the one control that breaks the chain there.
- [ ] You correctly identify the **expired-cert failure as a loss of detection** (an availability /
  accounting failure), not just "bad luck."
- [ ] Your bottom line states that **no single control failed** — the breach required a chain — and you
  can explain why naming only "they didn't patch" is incomplete.
- [ ] You scored your README prediction against the reveal and noted what you missed.

## Deliverables
`principle-autopsy.md` — the one-page per-hop finding (failure · principle · breaking change + bottom
line). This is a genuine analyst artifact; write it like one, not like a worksheet. Commit it. Do not
commit any private host details from your cert-checker runs.

## Automate & own it
**Required — a small reviewable script.** One whole hop failed because nobody noticed an **expired
certificate** until it was far too late. Turn that lesson into a tiny tool: a Python script
`cert_check.py` that takes a hostname, opens a TLS connection, reads the certificate's expiry date, and
**prints how many days remain (and exits non-zero if it's expired or expires within N days).** Run it
against a host you own (or `badssl.com`'s [expired-cert example](https://expired.badssl.com/) to see the
failure path). This is the Equifax blind spot, encoded so it can't silently recur on *your* systems.
Have a model draft it; **review every line** — confirm it actually fails on the expired host for the
right reason — and commit *your* reviewed version. (Standard library only: `ssl` + `socket` +
`datetime`.)

## AI acceleration
Before writing the autopsy, ask a model to map the Equifax failures to principles, then audit it. It
will likely flatten the story to "they failed to patch" and miss the flat network and the
detection-blinding cert. Catching those two is the skill. Then paste in your `cert_check.py` and ask the
model to find an input that breaks it — a host with no cert, a connection timeout — and harden it.

## Connects forward
Every hop is a later module: the flat network → Threat Modeling and trust boundaries (12); least
privilege and segmentation → every host- and network-hardening lab; "logged but not detected" → the
detective-control thread that runs into the Defensive track. This autopsy is the analytical frame for
every breach you'll dissect from here on.

## Marketable proof
> "I analyze incidents through first principles — CIA, AAA, defense in depth, least privilege — and can
> show a breach as a *chain* of failed controls, not a single villain. I can explain why Equifax needed
> the unpatched flaw, the flat network, *and* the blinded monitoring to lose 147M records."

## Stretch
- Re-render the autopsy for a *different* documented breach (pivot from the
  [CISA Known Exploited Vulnerabilities catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog))
  and compare: which principles fail in *every* breach, and which are breach-specific?
- Extend `cert_check.py` to take a list of hosts and print a sorted "soonest to expire" table — the
  start of a real monitoring-the-monitors check.
