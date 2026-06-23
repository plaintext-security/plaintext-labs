# Lab 09 — Detect AD Attacks with Sigma and Chainsaw

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/09-detecting-ad-attacks
make up      # start the chainsaw container with EVTX data + Sigma rules
make demo    # run chainsaw over the EVTX samples, then score the rules on a held-out corpus
make shell   # interactive shell to write and test your own rules
make down
```

The `data/evtx/` directory contains real-shaped EVTX (JSON-shaped) events for each AD attack:
- `kerberoast-4769.json` — Event 4769 with RC4 etype (Kerberoast)
- `asrep-4768.json` — Event 4768 with PreAuthType=0 (AS-REP roast)
- `dcsync-4662.json` — Event 4662 with DS-Replication (DCSync)
- `pth-4624.json` — Event 4624 Type 3 with NtLmSsp (PTH)

The `data/rules/` directory contains the Sigma rules to study and extend. `data/heldout/events.json`
is a **held-out** labelled corpus — attack events the rules must catch and benign near-misses they
must NOT fire on — that the rules were never written against; `scripts/eval_detections.py` scores the
rules against it and is the regression gate.

> This lab analyses bundled telemetry. No live attack systems involved.

## Scenario

You are a detection engineer. A red team has finished an engagement against a Windows domain and
handed you the attack timeline. Your job: write Sigma rules that would have detected each step of the
attack path from module 08, validate them against the bundled samples with chainsaw, and then prove
they are *effective* — not just that they fire on the demo attack, but that they stay quiet on the
benign 4769/4662/4624 noise that drowns a real domain. Coverage on the demo is the easy half;
effectiveness on a held-out benign+attack corpus is the half that keeps a rule out of the noise.

## Do

1. [ ] **Run the demo.** `make demo` runs chainsaw over the EVTX samples using the bundled rules, then
   scores the rules against the held-out corpus. Read both halves — which rules fired on the attack
   samples (coverage), and the scorecard (effectiveness). Note that the demo set is the data the rules
   were *written against*: of course they fire on it.

2. [ ] **Study the Kerberoast rule.** Open `data/rules/kerberoast.yml` and account for every field:
   why does the `logsource` matter, which single event field+value is the discriminator for
   Kerberoasting (etype `0x17`, not the SPN), and is the ATT&CK tag correct? Confirm the field in the
   raw event lines up with the rule's filter.

3. [ ] **Write the DCSync Sigma rule.** Fill in the `dcsync-stub.yml` stub. You'll need: the right
   Event ID for directory-service access, the extended-right GUID that identifies replication, and an
   exclusion so legitimate DC-to-DC replication (machine accounts) doesn't fire it. Tag the correct
   sub-technique. Validate it with chainsaw against the DCSync EVTX.

4. [ ] **Write the PTH Sigma rule.** Create `data/rules/pth.yml` to catch a pass-the-hash logon.
   Decide which event, logon type, and authentication package signal an NTLM network logon, then add
   exclusions so machine accounts, the null SID, and localhost don't generate noise. Validate against
   the PTH EVTX.

5. [ ] **Score against the held-out corpus.** Run `make eval`. This scores all four rules against
   `data/heldout/events.json` — a labelled set of attack events each rule must catch **and benign
   near-misses each must NOT fire on**: the AES (`0x12`) ticket for the *same* service SPN, the `DC2$`
   machine account doing legitimate replication, the normal `PreAuthType=2` AS-REQ, the Kerberos
   file-share logon, the machine-account NTLM service auth. Read the scorecard: **recall** (did it
   catch every attack?), **precision**, and **FP-rate** (did it stay quiet on the benign noise?). A
   rule that fires on the demo attack but also on its benign twin is alert fatigue, not a detection.

6. [ ] **See the gate go RED, then keep it GREEN.** Run `make gate` — it scores a deliberately
   too-broad ruleset (the exclusions dropped) and the gate exits non-zero, because each rule now fires
   on its benign near-miss (a false positive). That is exactly how a detection rots into noise:
   coverage stays fine, effectiveness collapses. Now make sure *your* rules keep `make eval` GREEN —
   if you ever loosen a filter and a benign near-miss starts matching, the gate catches it.

7. [ ] **Document the audit policy requirement.** For each of the four rules, write down which specific
   audit category must be enabled on the DC for the event to appear at all. This is the prerequisite
   most environments miss — without it the event never logs and no Sigma rule can ever fire.

## Success criteria — you're done when

- [ ] All four Sigma rules (kerberoast, AS-REP, DCSync, PTH) fire on their respective EVTX samples.
- [ ] `make eval` is GREEN: every rule catches every attack in the held-out corpus (recall 100%) and
      fires on **none** of the benign near-misses (FP-rate 0%).
- [ ] You have *seen the gate go RED* via `make gate` — a gate you've only watched pass isn't a gate.
- [ ] Each rule is tagged with the correct ATT&CK technique, and you have documented the required
      audit policy for each rule.

## Deliverables

`data/rules/kerberoast.yml`, `dcsync.yml`, `asrep.yml`, `pth.yml` — the four Sigma rules. Commit them.
Commit `detection-report.md` — the audit policy requirements, your held-out scorecard (recall /
precision / FP-rate per rule), and which benign near-miss each exclusion suppresses. Commit the
held-out corpus and `scripts/eval_detections.py` (the `make eval` / `make gate` gate) alongside them so
the detections can't silently regress.

## Automate & own it

**Required.** Don't stop at rules that fire — turn them into a **regression gate** so they can't
silently rot into noise. The lab ships exactly this: `scripts/eval_detections.py` scores the rules
against the **held-out** benign+attack corpus and **exits non-zero on any missed attack (recall < 100%)
or any benign false positive**, surfaced as `make eval` (gate on the good rules) and `make gate`
(prove it goes RED on a too-broad copy). Extend it: add a held-out case for the honeytoken SPN, or
wire `make eval` into a GitHub Actions workflow so a rule that regresses into noise can't merge. AI
drafts the precision/recall arithmetic and the scorecard table; **you own the metric choice (recall on
the attack class plus FP-rate, not raw accuracy), the held-out wall — the corpus must stay distinct
from the demo set — and the gate's fail-closed direction.** Commit the gate with the rules. (Honor
system — the gate guards *you* against regressions; there is no grader.)

## AI acceleration

After writing each rule, paste it into a model and ask: "What benign Windows activity could make this
rule fire?" The model is good at enumerating FP scenarios for well-known events (the AES ticket for the
same SPN, the machine-account replication, the Kerberos file-share logon). Turn each one into a labelled
**benign** entry in your held-out corpus, then add the filter that suppresses it and re-run `make eval`
to confirm the FP is gone and no attack was lost. A model labelling its own test set is the
contamination this whole exercise guards against — you own the labels and the metric.

## Connects forward

These Sigma rules are the detection layer for the hardening controls in module 10; the audit policy
requirements you documented are part of that hardening checklist. Module 11 covers integrating these
detections — and this held-out eval gate — into a continuous monitoring architecture.

## Marketable proof

> "I write Sigma detections for Active Directory attacks — Kerberoasting, DCSync, pass-the-hash —
> validate them against real EVTX telemetry with chainsaw, and gate them against a held-out
> benign+attack corpus so a rule can't regress into noise and silently merge."

## Stretch

- Write a honeytoken detection: a Sigma rule that fires on any Event 4769 for a specific honeytoken SPN
  (e.g. `HoneyToken/decoy.corp.example`). By definition, any match is attacker activity. Add a held-out
  attack case for it and compare its reliability to the rate-based Kerberoasting detection.
- Research **Wazuh** integration: how would you push these Sigma rules into Wazuh's ruleset? What is the
  conversion path from Sigma YAML to Wazuh XML rule format?
