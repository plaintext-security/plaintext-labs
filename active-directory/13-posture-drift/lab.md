# Lab 13 — AD Posture Drift & Steady-State

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

The detector runs in **two collection modes**. The default seed-file mode is deterministic (great
for the gate and CI); the `*-live` targets read posture straight off the bundled Samba DC over LDAP.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/13-posture-drift
make up           # start the Samba DC + the detector/tools container
make demo         # deterministic: clean -> introduce drift -> detector names every regression
make drift        # mutate the seed posture to simulate a month of decay (CI-safe)

# --- the real-DC path -----------------------------------------------------------------------
make baseline-live  # snapshot the LIVE DC posture (ldap3) into data/baseline.live.json
make drift-live     # introduce REAL drift on the DC via samba-tool (new SPN + unexpected DA)
make detect-live    # collect LIVE posture over LDAP and diff it against your baseline (exit 1 on drift)
make shell          # interactive shell
make down
```

The lab provides:
- A Samba4 DC (the same image built in Module 02) reachable at `dc01.corp.local` / `10.10.0.10`.
- A detector/tools container with `ldap3`, `ldapsearch`, `samba-tool`, and `cron`.
- `data/baseline.json` — the **declared baseline** (the committed "this is good" posture: Kerberoastable accounts `[]`, dangerous ACEs `[]`, privileged-group rosters, krbtgt age threshold).
- `drift-detect.py` — the detect→diff loop. `collect_observed_live()` reads the live DC via ldap3 (kerberoastable SPNs, AS-REP/unconstrained UAC bits, privileged-group rosters, krbtgt age); `--live` / `make detect-live` exercises it for real.
- `bin/drift-introduce.sh` — applies a month of decay: in seed mode it mutates `data/observed.json`; with `--live` (`make drift-live`) it runs real `samba-tool spn add` / `group addmembers` against the DC.

> **Note on Adalanche.** The optional attack-graph corroboration step uses Adalanche, which is not bundled (it ingests a live DC); run it yourself against `make up`'s DC if you want the graph view. The drift loop itself does not require it.

> **Authorization.** Runs against your own lab domain only. The `drift-introduce.sh` mutations and any
> reconciliation (rotating krbtgt, removing ACEs, ejecting accounts) are destructive — never run them
> against a domain you do not own or have explicit written permission to modify.

## Scenario

You are the AD security lead for the `corp.local` domain. The hardening sprint (Module 10), the tiered design (Module 11), and the brownfield rollout (Module 12) are *done* — the domain is hardened and PATH-001 is dead, today. The CISO's next question is the one that actually matters operationally: **"Will it still be hardened next month, and how will we know the day it isn't?"** Your job: pin the current hardened posture as a committed baseline, build a scheduled detector that diffs the live domain against it, simulate a month of decay, and prove your detector catches every regression — then reconcile each one (bless it into the baseline or re-enforce) and prove steady-state is restored.

## Do

1. [ ] **Pin the declared baseline.** Run `make demo`. Inspect `data/baseline.json` — the committed hardened posture (Kerberoastable accounts, no-preauth accounts, unconstrained-delegation principals, dangerous ACEs, privileged-group rosters, krbtgt age + threshold). Confirm it matches the live DC right now (the detector reports **no drift** on a clean domain). This is your declared state, version-controlled. *Decide the thresholds yourself* — e.g. krbtgt max age (180 days per ATT&CK M1015, or stricter); justify your choice in a comment.

2. [ ] **Run and own the detector loop: detect → diff.** The shipped `drift-detect.py` implements it: it captures the **observed** posture and diffs it against `baseline.json`, emitting a per-fact delta (never a score), with both sides sorted/normalized so the diff shows real change, not reordering noise. Read `collect_observed_live()` and confirm each fact maps to a real LDAP query (SPN search, the `userAccountControl` bit-and OID for AS-REP/unconstrained, group `member` reads, krbtgt `pwdLastSet` → age). Then prove the two modes agree: `make detect` (seed) and, after `make up`, `make detect-live` (real ldap3 collection off the DC) run the **same** diff logic. On a clean state it must emit an empty delta.

3. [ ] **Introduce drift, two ways.** Seed mode: `make drift` mutates `data/observed.json` (new `svc-newdb` SPN, re-added `GenericWrite` on `Finance-Managers`, an unexpected `Domain Admins` member, krbtgt aged past threshold) — deterministic, so the gate is reproducible. Real-DC mode: `make drift-live` runs actual `samba-tool spn add` and `group addmembers` against `dc01.corp.local`, then `make detect-live` collects and names the drift over LDAP. You are **not** told the exact set — your detector must find them.

4. [ ] **Detect the drift — diff catches every regression.** Re-run your detector. It must emit a delta that names **each** introduced change as a concrete fact: *new Kerberoastable SPN on `svc-newdb`*, *`GenericWrite` re-added on `Finance-Managers`*, *`<user>` joined `Domain Admins`*, *krbtgt age over threshold*. Map each to its ATT&CK technique (the ACE/group-add → T1098; the stale krbtgt → standing T1558.001 risk). Save the delta as `drift-report.md`. If your detector misses one, fix the detector — a drift detector that misses drift is the failure the module is about.

5. [ ] **Corroborate with the attack-graph view.** Re-run **Adalanche** against the drifted DC and show the graph now contains a privesc edge to Domain Admin that the t=0 graph did not. This is the same delta seen as a graph — proof the drift actually *reopened a path*, not just changed an attribute. (Optional but recommended: diff the Adalanche path output against a t=0 capture.)

6. [ ] **Reconcile every delta — bless OR re-enforce.** For each drift item, adjudicate (this is the judgment half, and it must be explicit per item):
   - **Sanctioned?** (e.g. `svc-newdb` is a legitimate new app) → **bless it into the baseline**: update `baseline.json` and commit with a message recording *who decided and why*. The baseline is now the decision log.
   - **Real drift?** (the re-added ACE, the unexpected DA, the stale krbtgt) → **re-enforce**: remove the ACE, eject the account, rotate krbtgt (twice, per M1015). Then re-run the detector and prove that item is **back at steady-state**.

   Record each decision and its outcome in `drift-report.md`. Do not leave any delta un-adjudicated — that's the alert-fatigue failure.

7. [ ] **Prove steady-state restored.** Re-run the detector after reconciliation. It must emit a **clean (empty) delta** against the (now possibly updated) baseline, and re-run Adalanche to show the privesc edge is gone again. Steady-state is the deliverable, not just detection.

8. [ ] **Schedule it.** Wire the detector to run nightly via `cron` (the `crontab(5)` five-field schedule) inside the tools container, writing its delta report to a dated file and exiting non-zero when drift is found (so it can later gate/alert). A detector you run by hand is just another one-time audit; scheduling is what makes "is it *still* hardened?" a question the system answers without you.

## Success criteria — you're done when

- [ ] `data/baseline.json` is a committed, normalized declared baseline with *justified* thresholds (krbtgt age, etc.).
- [ ] The detector emits an **empty delta on a clean domain** (no false positives) and a **fact-level delta** (not a score) when drift exists.
- [ ] After `make drift`, your detector named **every** introduced regression and you mapped each to its ATT&CK technique.
- [ ] Adalanche shows the privesc edge appear under drift and disappear after reconciliation.
- [ ] **Every** delta was adjudicated — each blessed (baseline updated, with a who/why commit) or re-enforced (remediated, steady-state re-proven). None ignored.
- [ ] The detector runs on a **schedule** (cron) and exits non-zero on drift.

## Deliverables

`drift-detect.py` (the detect→diff detector) + `data/baseline.json` (the declared baseline, with your threshold justifications and any blessed updates as commits) + `drift-report.md` (the delta after `make drift`, each item mapped to ATT&CK, the bless/re-enforce decision for each, and the steady-state-restored proof) + the cron entry. Commit these. Lab artifacts (graph dumps, tickets, hashes) stay out of commits.

## Automate & own it

**Required** — and in this lab the automation *is* the deliverable, so the "own it" bar is the whole point. `drift-detect.py` must implement the full **detect → diff → reconcile-report** loop, scheduled. Have a model draft the per-fact LDAP queries, the JSON diff, the cron wiring, and the report formatting. Then own three things the model gets wrong: (1) it will try to **diff a score** instead of the facts — force it to diff the structured posture facts, because the score hides *which* control moved; (2) it will propose **auto-revert on any drift** — reject that, the reconcile step is *human adjudication* (bless-or-enforce), and a blind `apply` that reverts a sanctioned change is its own outage; (3) it will **invert the krbtgt-age / ACL checks** — verify that a fresh krbtgt scores clean, a stale one scores drift, and an *absent* dangerous ACE is *not* a finding. You set the thresholds, you read every delta, you decide bless-or-enforce. Commit it.

## AI acceleration

Beyond the build above: ask a model to summarize, from your `drift-report.md`, a one-paragraph "posture change since last baseline" note for the CISO — what drifted, what you blessed, what you re-enforced. It's good at the prose; verify it didn't silently drop a delta or mislabel a sanctioned change as a regression (or vice-versa). The standing rule holds: the model writes the detector and the summary; **you** own the baseline, the thresholds, and every bless-or-enforce call. A drift detector is only as trustworthy as the human who adjudicates its alerts — automate the detection, never the judgment.

## Connects forward

This closes Track 06's arc with a *fourth* dimension the capstone otherwise lacks: Modules 08–12 prove the path **is** closed; this proves it **stays** closed, with a dated trail. The detect→diff→reconcile loop is the same steady-state discipline Track 11 (ZTNA) applies to policy drift and the cloud tracks apply to posture drift — AD is one instance of a pattern every hardened system needs. The `baseline.json`-as-decision-log practice is the operational form of the "if it isn't in version control it isn't real" thesis Module 10 states.

## Marketable proof

> "I build scheduled Active Directory posture-drift detectors: a version-controlled hardened baseline, a nightly re-audit that diffs observed security facts (Kerberoastable SPNs, dangerous ACEs, privileged-group rosters, krbtgt age) against it, attack-graph corroboration with Adalanche, and a reconcile loop that adjudicates every delta — bless-into-baseline or re-enforce — so I know within a day when the domain drifts back toward exploitable, and can prove it returned to steady-state."

## Stretch

- Turn the detector into a **CI gate**: run it in GitHub Actions on a schedule (cron workflow) against the `make up` lab DC, fail the build on un-blessed drift, and open an issue with the delta. This is the steady-state analog of Module 10's posture gate.
- Extend the baseline to track **GPO drift**: snapshot the security-relevant GPO settings (the Deny-logon user-rights from Module 12, audit policy from Module 09) and diff those too — drift isn't only objects and ACEs, it's the policies that enforce them being unlinked or edited.
