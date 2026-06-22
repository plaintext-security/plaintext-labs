# Lab 12 — Threat-Modeling the System You Built

*Variant D · concept autopsy, applied. [← Back to the module concept](README.md)*

## Setup
This lab ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. No Docker required —
you'll fill in a template and validate it.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/foundations/12-threat-modeling
make demo                          # validate the example template + print the STRIDE guide
cp data/threat-model-template.md threat-model.md
# ... fill it in ...
make validate FILE=threat-model.md # check coverage: boundaries + all 6 STRIDE letters + mitigations
```

## Scenario
You're not modeling an imaginary app. You're modeling **the small lab system you stood up earlier in
this track** — the isolated VM and containers from Phase 1, or, if you'd rather model something with a
clear front door, the simple web app shape (browser → web server → database with user logins) the
template is built around. Either way: a *real* system whose pieces you understand, because the whole
point is that you can draw its boundaries honestly.

This is the Target lesson made personal. Target's fatal crossing was a connection it had on paper and
never treated as a boundary. Your job is to find *yours* before an attacker does — on the whiteboard,
where it's cheap.

> If you later point any attacking tool at this system (you will, in later tracks), keep it on your own
> machine. Only test systems you own or have explicit written permission to test.

Each step runs the same rhythm as the module: **draw → ask STRIDE → write the mitigation**.

## Do

1. [ ] **Draw the data flow (text is fine).** List the **elements** (browser, web server, database —
   or your VM, your containers, the host), the **flows** between them with their protocol
   (e.g. `Browser → Web Server: HTTPS/443`), and — the load-bearing part — the **trust boundaries**
   those flows cross. Mark **at least two**. Ask at each flow: *does data here move from less-trusted to
   more-trusted?* That's a boundary. (The Target one to learn from: a third-party / vendor connection
   reaching an internal network is a boundary even when it "feels internal.")

2. [ ] **Walk STRIDE at each boundary.** For every crossing, go through all six letters and write **at
   least one concrete threat per letter** — concrete meaning "an attacker submits a forged session
   cookie to act as another user," not "spoofing could happen." Use the six questions from the module
   (S: can they impersonate? T: can they modify? R: can they deny it? I: can they read what they
   shouldn't? D: can they take it down? E: can a low-priv foothold become high-priv?). The
   elevation-of-privilege one is Target's pivot — name yours.

3. [ ] **For each threat, write a mitigation and the CIA property it protects.** "Parameterized
   queries → protects Integrity." "Scope the vendor/service account to least privilege → protects
   against Elevation." This closes the loop back to first principles and is what makes the model
   *actionable* rather than a worry list.

4. [ ] **Pick your top two controls to prioritise** — the ones that break the most threats. A real model
   doesn't fix everything at once; it says *what to do first*. Justify each by the threats it kills.

## Success criteria — you're done when
- [ ] Your diagram marks **at least two trust boundaries**, and you can say in one sentence why each is a boundary.
- [ ] You have **at least one concrete threat for every STRIDE letter** (S, T, R, I, D, E).
- [ ] Each threat has a **mitigation tied to a CIA property**.
- [ ] You named the **elevation-of-privilege** threat that is your system's version of Target's flat-network pivot.
- [ ] `make validate FILE=threat-model.md` passes (boundaries + all 6 letters + mitigations + CIA present).

## Deliverables
`threat-model.md` — the one-page model: the data-flow sketch, the STRIDE table
(threat → trust boundary → mitigation → CIA property), and your top-two controls. This is a genuine
engineering artifact — write it like one. Commit it to your portfolio repo. Do **not** commit anything
the model references that's sensitive (real credentials, real internal hostnames).

## Automate & own it
**Required.** Hand a model your data-flow description from step 1 and ask it for a full STRIDE pass.
You'll get a fast, confident list. Now do the work that makes it *yours*: **prune** the threats that
don't apply to your system, **add** the ones it couldn't know (your real trust boundaries, your actual
flows), and record — in the model's "AI reconciliation" section — what you **kept, cut, and added, and
why**. AI drafts → you review every line → you own the page. That reconciliation note is the proof you
did the thinking, not the model.

## AI acceleration
The pruning *is* the learning. A model enumerates plausible STRIDE threats faster than you can type
them, which is exactly its value as a brainstorming partner — and exactly its danger if you ship its
list unread. Catch it inventing threats for flows you don't have, and catch the threats it misses
because it can't see your system. If you can explain why each cut and each addition was right, you've
learned the module.

## Connects forward
This is the lens you bring to **every later track** — and each track's capstone is, in effect, a
threat modeled and then proven. Spoofing becomes the auth attacks of the offensive track; information
disclosure becomes the data-exfil paths of the cloud track; the trust-boundary habit becomes network
segmentation and zero-trust. You'll also carry this straight into **this track's capstone**, where the
one-page STRIDE model is one of the required artifacts.

## Marketable proof
> "Before I reach for a single tool, I threat-model a system with STRIDE — assets, trust boundaries,
> concrete threats, and mitigations tied to CIA. I can point at the crossing nobody guarded the way
> Target's vendor connection was the crossing nobody guarded."

## Stretch
- Re-model the same system **as an attacker** (an attack tree): pick your elevation-of-privilege threat
  and decompose, step by step, how you'd actually achieve the pivot — the offensive mirror of the
  defensive model.
- Read one more real concept-autopsy: pick a public breach post-mortem (e.g. from the [CISA known
  exploited catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)) and identify, in one
  paragraph, the trust boundary a STRIDE pass would have flagged.
