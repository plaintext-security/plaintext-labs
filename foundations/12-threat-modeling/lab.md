# Lab 12 — Threat-Modeling a Small Application

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/12-threat-modeling
make demo   # validate the STRIDE template + print the threat modeling guide
```

No Docker required. Copy the template and validate your completed model:
```bash
cp data/threat-model-template.md threat-model.md
# ... fill it in ...
make validate FILE=threat-model.md
```

Optionally model a real vulnerable app:
```bash
docker run --rm -d -p 3000:3000 bkimminich/juice-shop
```

## Scenario
Model a simple web app: a browser → a web server → a database, with user logins. Produce a
data-flow diagram and a STRIDE threat list.

> If you point any later-track tooling at this app, keep it on your own machine — never at
> systems you don't own.

## Do
1. [ ] Draw the data flow (text is fine): the **elements** (browser, server, DB), the
   **flows** between them, and the **trust boundaries** those flows cross.
2. [ ] Walk **STRIDE** per element/flow and write at least one concrete threat for each
   letter (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service,
   Elevation of privilege).
3. [ ] For each threat, note a **mitigation** and which CIA property it protects.

## Success criteria — you're done when
- [ ] Your diagram marks at least two trust boundaries.
- [ ] You have at least one concrete threat for every STRIDE letter.
- [ ] Each threat has a mitigation tied to a CIA property.

## Deliverables
`threat-model.md`: the data-flow sketch and a STRIDE table — threat → trust boundary →
mitigation → CIA property protected.

## AI acceleration
Give a model your data-flow description and ask for a STRIDE pass; then prune its list to
what's real for *this* app and add what it missed. The pruning is the learning.

## Connects forward
This is the lens you bring to every later track — and each track's capstone is, in effect,
a threat modeled and then proven.

## Marketable proof
> "I threat-model a system with STRIDE — assets, trust boundaries, threats, and mitigations
> — before reaching for a single tool."

## Automate & own it
**Required.** Have a model generate a STRIDE pass from your data-flow description, then prune and
correct it to what's real for *this* app — commit *your* owned model, noting what you cut and why.

## Stretch
- Re-model the same app as an attacker (an attack tree): pick one STRIDE threat and
  decompose how you'd actually achieve it.
