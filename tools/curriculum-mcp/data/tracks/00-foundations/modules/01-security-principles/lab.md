# Lab 01 — Reason About a Breach with First Principles

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/01-security-principles
make demo   # print breach-analysis template + recent CISA KEV entries
```

No Docker required. Python 3 only.

## Scenario
Pick a documented breach (a vendor post-mortem, or pivot from the
[CISA Known Exploited Vulnerabilities catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog))
and dissect it through the principles — building the analytical muscle before you have tools
to lean on.

## Do
1. [ ] Summarise the breach in three sentences: what was accessed, how, and what failed.
2. [ ] Map it to the CIA triad: which property (or properties) was violated, and how?
3. [ ] Identify the failed control(s) and name the principle each represents (least
   privilege? defense in depth? authentication?).
4. [ ] Propose two controls that would have broken the attack chain, and state which CIA
   property each protects.

## Success criteria — you're done when
- [ ] You can state which CIA properties were violated and why.
- [ ] Every proposed control maps to a named principle and a CIA property.
- [ ] You can explain the attack as a chain, not a single event.

## Deliverables
`breach-analysis.md`: the three-sentence summary, the CIA mapping, and your two controls
with the principle each embodies.

## AI acceleration
Have a model produce its own principle-mapping of the same breach, then compare — where it
disagrees with you is where the learning is. Settle it by going back to the source.

## Connects forward
This is the analytical frame for every track's threat model and the Threat Modeling capstone
(module 12).

## Marketable proof
> "I analyse incidents through first principles — CIA, least privilege, defense in depth —
> not just tool output."

## Automate & own it
**Required.** Have a model produce its *own* CIA/principle mapping of your breach, then correct
and annotate it — and commit *your* reconciled version. Owning the disagreement is the point.

## Stretch
- Re-frame the breach from the attacker's side: which principle did they exploit, and what
  was the cheapest control that would have stopped them?
