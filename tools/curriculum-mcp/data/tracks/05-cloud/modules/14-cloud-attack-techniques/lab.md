# Lab 14 — Simulate Cloud Attack Techniques

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — the environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/14-cloud-attack-techniques
make up       # start LocalStack + the lab container
make demo     # run the attack simulation and print CloudTrail-shaped output
make shell    # drop into the lab container for manual exploration
make down     # stop everything when done
```

The environment is a LocalStack container (fake AWS) plus a lab container with `awslocal`,
`stratus-red-team`, and `pacu` installed. `make demo` runs `simulate.sh`, which fires attacker-like
API calls against LocalStack and prints the CloudTrail JSON each call would generate.

## Scenario
Meridian Financial's security team has received an alert: a developer's long-lived AWS access key
(`AKIAIOSFODNN7EXAMPLE`) was found in a public GitHub repository. The team wants to understand
exactly what an attacker armed with those credentials would do — and what the API calls would look
like in CloudTrail before any detections fire.

Your goal is to walk the attack chain from credential use through data collection to exfiltration
staging, and map each step to its ATT&CK technique and its distinguishing CloudTrail event fields.

> Only test systems you own or have explicit written permission to test. This lab uses
> LocalStack — a local AWS simulator — so no real AWS resources or credentials are involved.
> Apply the same restraint on any real account: work only in dedicated test environments, and
> tear down everything when the exercise is done.

## Do
1. [ ] **Orient on the session.** Review `data/pacu-session.json`. What IAM identity does the
   compromised key belong to? What is the attached policy? Which module findings suggest the
   attacker has a path to privilege escalation? (Hint: look for `iam:PassRole` or
   `sts:AssumeRole` with a broad trust policy.)

2. [ ] **Enumerate interactively.** With the lab container running (`make shell`), enumerate the
   LocalStack environment's IAM users and S3 buckets the way an attacker with the leaked key
   would. Note the exact API calls you are making — those are what end up in CloudTrail.

3. [ ] **Detonate T1078.004.** Use `simulate.sh` to fire the role-assumption technique, then
   examine the CloudTrail JSON output. Which `eventName` signals the role assumption? What
   fields in `userIdentity` change between the original key's calls and the assumed-role calls?

4. [ ] **Detonate T1530.** Drive `simulate.sh` to run the bulk S3 object-download technique,
   which calls `GetObject` across every object in the seed buckets. What pattern in `eventName`,
   `requestParameters.key`, and `sourceIPAddress` would a detection rule key off? Why isn't a
   single `GetObject` a finding, but fifty in thirty seconds is?

5. [ ] **Detonate T1537.** Drive `simulate.sh` to run the S3 exfiltration-staging technique,
   which adds a bucket replication rule pointing at an external destination (a second LocalStack
   bucket acting as the attacker's account). Identify the `eventName` and the `requestParameters`
   field that exposes the external destination. Which ATT&CK sub-technique does this most
   precisely match?

6. [ ] **Map to ATT&CK.** For each of the three techniques you detonated, write one sentence
   describing the minimum CloudTrail event signature — the smallest set of fields a detection
   rule needs to fire reliably without too many false positives.

## Success criteria — you're done when
- [ ] You can explain what `userIdentity.type: AssumedRole` indicates vs. `IAMUser` in CloudTrail.
- [ ] You can identify the three API calls (one per technique) that are clearest attack signals.
- [ ] You have a written ATT&CK mapping for each simulated technique with the key log fields.
- [ ] You have reviewed `data/pacu-session.json` and identified at least one privilege-escalation
  finding the session exposes.

## Deliverables
`attack-mapping.md`: one table row per technique (T-ID, eventName(s), key fields, why it fires vs.
normal traffic). Commit `attack-mapping.md` alongside your `automate.sh`.

## Automate & own it
**Required.** Write a shell or Python script (`automate.sh` or `automate.py`) that:
1. Calls the three LocalStack simulation endpoints in sequence.
2. Captures the CloudTrail JSON output for each.
3. Prints a one-line summary: technique ID, the triggering `eventName`, and the attacker's
   `sourceIPAddress`.

Have a model draft the script. Before committing, verify each API call fires against the running
LocalStack container and the output actually contains the fields your summary line reads. If the
model references a CloudTrail field that doesn't appear in the real output, that's a hallucination —
fix it. You own every line.

## AI acceleration
Feed the `data/pacu-session.json` to a model and ask: "What ATT&CK Cloud techniques does this
session expose, and what are the highest-risk API calls?" Use its output as a first-pass enumeration;
verify each claimed technique against the ATT&CK technique card's detection guidance before writing
it up. Models frequently confuse `iam:ListRoles` (benign enumeration) with `sts:AssumeRole`
(actual technique execution) — you need to be the one who knows the difference.

## Connects forward
Module 15 (Cloud Logging & Detection) takes the CloudTrail output you generated here and builds
Sigma rules against it. The attack signatures you mapped in step 6 are exactly the logic you'll
encode as detection rules. Module 16 (Cloud IR) hands you a richer CloudTrail corpus and asks you
to reconstruct the same attack chain from the other direction.

## Marketable proof
> "I simulate MITRE ATT&CK Cloud techniques in a safe, local environment, map each to its
> CloudTrail signature, and can describe precisely what a detection rule needs to fire on — and
> what it must not fire on."

## Stretch
- Extend `simulate.sh` to chain the three techniques in order and output a single JSON array of
  events in timestamp order. This is your synthetic CloudTrail log — hand it to module 15's
  detection script and confirm it fires.
- Explore what Stratus Red Team's `--cleanup` flag does. Why is cleanup a security discipline, not
  just a housekeeping step?
