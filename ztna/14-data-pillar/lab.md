# Lab 14 — Data, the Last Pillar: label-based authorization and exfil detection

> **Hands-on lab.** Environment: `plaintext-labs/ztna/14-data-pillar`.
> Objective: **make the classification label an access-control input** — extend OPA (Module 08) with a
> role × classification policy that fails closed on a missing label, and extend Sigma (Module 09) with a
> detection for bulk reads of restricted data. Target: **~100–120 min**, one finish line. This is a
> **reference lab** — the exact `opa` and `sigma-cli`/`detect.py` toolchain from Modules 08 and 09,
> pointed at a new input.

---

## ✈ Flight card — the 7 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The `classification` label IS an access-control input, not metadata.** | Reading it is not enough — the policy decides *from* it, the same way it decides from a role claim. |
| 2 | **`default effective_classification := "restricted"` is the one line that makes absence fail closed.** | Break it and an unlabeled record silently becomes world-readable — the fail-open trap, one config line deep. |
| 3 | **Role × classification: analyst/auditor read internal; only data-officer/admin read restricted.** | `deny` overrides `allow`, and querying `deny` — not just "not allow" — is the must-deny proof. |
| 4 | **OPA decides ONE request; Sigma decides a SESSION'S volume.** | A stolen-but-valid credential passes OPA on every single read — count across the session is the only tell. |
| 5 | **The dangerous session looks identical to the legitimate one: same device, same country, same role.** | Volume is the only anomaly (Snowflake, 2024: stolen creds, no MFA, no data-layer guardrail caught the volume). |
| 6 | **This module closes NIST 800-207's fifth pillar.** | Identity (02) → device (03) → network (07) → workload (12) → **data (14)** — the set an enterprise buyer expects covered end to end. |
| 7 | **The real handles:** roles `analyst`/`auditor`/`data-officer`/`admin`; sessions `sess_D1` (dpatel, normal, 3 restricted reads) vs `sess_D2` (dpatel, overnight burst, 8 reads); threshold `> 5`. | These are the exact strings in the data — the module prose used the general shape. |

*(If you can explain all seven cold at the end — especially #2 and #4 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [label-based authorization section](README.md#label-based-authorization-the-same-opa-a-new-input) and
> [the volume signal section](README.md#detecting-exfil-shaped-access-the-same-sigma-a-new-signal).

---

## Warm-up — answer before you start the containers (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A record's `classification` field is missing entirely — nobody wrote a policy rule for "no label."
   Should that record be readable by an ordinary authenticated role? Why is "no rule fired" a dangerous
   answer here specifically?
2. `dpatel` (a legitimate `data-officer`) reads 3 restricted records at reasonable hours, then reads 8
   more at 2 AM from the same device, same account, same country. Which OPA query, run against any one
   of those 11 reads, tells you something is wrong? (Trick question — read it twice.)
3. Name one control a CASB, a DLP-egress scanner, or a customer-managed encryption key (CMK/BYOK) would
   add here that neither the OPA policy nor the Sigma rule in this lab can give you.

---

## Setup

This is a **reference lab** with a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs the **same two
engines** as Modules 08 and 09 — real `opa` (pinned `openpolicyagent/opa:0.68.0`) and the `sigma-cli` +
`detect.py` teaching matcher — pointed at a new input: a `classification` label.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/14-data-pillar
make up        # start the OPA server + build the sigma/detect.py image
make demo      # run both halves: label-based decisions, then the bulk-read detection
make test      # opa test over data/policies/
make check     # the committed regression gate (check-data.sh)
make down      # stop it when you're done
```

> **▸ On track if:** `make demo` prints **PART 1** — six OPA decisions: `analyst` → public (`allow`),
> `analyst` → restricted (`allow` and `deny`), `data-officer` → restricted (`allow`), and the unlabeled
> record's `effective_classification` and `deny` for `analyst` — followed by **PART 2** (the Sigma rule
> against `data/access-logs.jsonl`), ending with a block of exactly **8** `[HIT]` lines, all tagged
> `session_id=sess_D2`, and the summary `Matched 8 of the events`.

> **Authorization note.** Everything here runs locally against bundled data you own — no external
> targets, no authorization needed. The corpus and access log are fictional (`data/records.json`,
> `data/access-logs.jsonl`) — this is honor-system, the same footing as Modules 08 and 09.

---

## Build it — read a little, do a little

### Step 1 — Read the corpus like the policy will

**Concept (30 sec):** Flight-card #1. Open `data/records.json` before you open the policy. In every
earlier module the access decision came from a claim about the *requester* (a role, a device posture, a
SPIFFE ID). Here it also comes from a claim about the *resource* — and that claim lives in the data, not
in code.

**Do it:** read `data/records.json`. Find `rec-003` (`restricted`), `rec-002` (`internal`), `rec-001`
(`public`) — and then find `rec-004` and `rec-009`, the two records where the classification field is
`null` and `"Restricted"` (wrong case) respectively. **Predict**, before running anything, whether an
`analyst` should be able to read each of the nine records. Then open `data/policies/data-classification.rego`
and confirm your predictions against `default allow := false`, the three `allow` rules, and the `deny`
rule.

> **▸ On track if:** you predicted `analyst` can read rec-001, rec-002, rec-006, rec-007 (public/internal)
> and **cannot** read rec-003, rec-005, rec-008 (restricted) — and, before reading the fail-closed section
> below, you flagged rec-004 and rec-009 as "not obviously public or internal, so I'm not sure" rather
> than defaulting them to public. That hesitation is the correct instinct — Step 3 makes it a rule.

### Step 2 — Prove the must-deny case

**Concept (30 sec):** Flight-card #3. `allow == false` and `deny == true` are not the same fact. The
finish line for label-based authorization is the second one: a merely-authenticated, non-privileged role
reading restricted data must produce a **fired deny**, not just an absent allow.

**Do it:** run the two queries by hand:

```bash
make eval POLICY=data/policies/data-classification.rego INPUT=data/inputs/analyst-read-restricted.json
```

Read the emitted `data` document for both `corp.data.allow` and `corp.data.deny`. Then run the same eval
against `data/inputs/data-officer-read-restricted.json` and confirm the opposite pattern.

> **▸ On track if:** `analyst` → restricted shows `allow: false` **and** `deny: true`; `data-officer` →
> restricted shows `allow: true`. If `deny` came back `false` for the analyst case, the rule isn't firing
> — re-check the role set in the deny rule, not just the allow rules.

### Step 3 — The centerpiece: break fail-closed, watch it fail open, fix it

**Concept (30 sec):** Flight-card #2 — the single load-bearing line in this whole lab. A record with no
recognizable label isn't "ungoverned" — it's supposed to be the **most** restrictive tier, by construction,
not by a rule someone remembered to write for every possible garbage value. Prove that by breaking it on
purpose.

**Do it:** open `data-classification.rego` and change the one line

```rego
default effective_classification := "restricted"
```

to

```rego
default effective_classification := "public"
```

Re-run the eval from Step 2 but point it at `data/inputs/analyst-read-unlabeled.json`, querying
`corp.data.effective_classification` and then `corp.data.allow`. **Watch the unlabeled record become
world-readable.** Record the one-line proof — the exact `"value"` you saw — in `fail-closed-proof.md`.
Then **restore the original line** and re-run both queries to confirm the fix.

> **▸ On track if:** with the bug planted, `effective_classification` reads `"public"` and `allow` reads
> `true` for the analyst reading the unlabeled record — a record that should be maximally protected is now
> the *easiest* one to read. With the line restored, `effective_classification` is back to `"restricted"`
> and `deny` is `true`. Broken → open, fixed → closed: that pair **is** the lesson, not the syntax — the
> exact shape as Module 08's fail-open centerpiece, one layer down.

!!! warning "This is how under-classified data becomes a breach"
    A record with no label, or a mis-typed one (`rec-009`'s `"Restricted"`, wrong case, is silently *not*
    the same string as `"restricted"` to Rego's case-sensitive match), is not a corner case — it is the
    everyday failure mode of any real data inventory: migrations lose tags, new tables ship unlabeled,
    someone fat-fingers a taxonomy value. The only defense is a default that resolves the unknown case to
    the *most* restrictive tier, and a test that asserts it — not a policy author's discipline.

### Step 4 — Detect the volume signal, then tune the threshold both ways

**Concept (30 sec):** Flight-card #4 + #5. OPA already proved every single read in `data/access-logs.jsonl`
was, on its own, a legitimate decision — `dpatel` is a `data-officer`, and a `data-officer` may read
restricted data. Nothing in the OPA layer is wrong about any *one* of those 11 reads. What's wrong is all
8 of them landing in one session at 2 AM. That's a different question, answered by a different tool.

**Do it:** run `make demo` (Part 2) or `make detect RULE=examples/zt-bulk-restricted-read.yml` and read
the `[HIT]` lines. Confirm they're all `sess_D2`, none are `sess_D1`. Then open the rule and change the
threshold `> 5` to `> 10` — re-run and watch the burst (8 reads) go **silent**, a missed compromise. Set
it back and instead try `> 2` — re-run and watch `dpatel`'s **normal** 3-read session (`sess_D1`) also
fire — a false positive that would train the SOC to ignore this rule. Restore `> 5`.

> **▸ On track if:** at threshold `> 5` you see exactly 8 hits, all `sess_D2`. At `> 10` you see **0**
> hits (a missed exfil). At `> 2` you see hits from **both** sessions (a false positive on ordinary work).
> Restoring `> 5` is not an arbitrary choice — it's the value that catches the real burst while staying
> silent on `dpatel`'s and `csingh`'s legitimate single-digit restricted reads elsewhere in the log.

> **▸ Note the boundary with Module 09.** This rule doesn't look at country, device, or time of day at
> all — the burst events even share the *same* device and country as the normal ones. A geo-rule like
> Module 09's would say nothing here. That's the point: label-based volume is a *different* signal than
> identity or geography, and a mature detection program runs both.

### Step 5 — Map the controls you can't self-host (assessed, not stood up)

**Concept (30 sec):** OPA and Sigma close the gap this track can build for free. A production data
pillar also layers controls that require a vendor platform or a KMS this lab cannot stand up in a
container — name them honestly rather than pretending the two engines above are the whole picture.

**Do it (write it, don't run it):** in your deliverable, map each of the following to what it would have
added to the Snowflake scenario, and to *this lab's* corpus/log if it existed for real:

- **CASB (Cloud Access Security Broker)** — a proxy/API-connector layer in front of the SaaS/warehouse
  that can enforce policy *and* log activity the app itself doesn't emit.
- **DLP egress scanning** — content inspection on the way *out* (a bulk CSV download, an API response
  over some row-count threshold) — the generalized, content-aware cousin of the count-based Sigma rule
  you just tuned.
- **Tokenization / format-preserving encryption** — restricted fields (SSNs, card numbers) stored as
  irreversible or format-preserving tokens, so a bulk *read* returns tokens, not the raw value, even if
  authorization was granted.
- **CMK/BYOK (customer-managed keys)** — the org holds the encryption key outside the vendor's control,
  so a vendor-side account compromise cannot decrypt data at rest without a *separate* key compromise.
- **Data residency** — controls on *where* a copy of restricted data is allowed to live at all, which a
  role/classification check alone says nothing about.

Label this section **assessed from a design, not something stood up** — same honesty as Module 03's
device-posture policy.

> **▸ On track if:** each control names the specific gap it closes that neither `data-classification.rego`
> nor `zt-bulk-restricted-read.yml` can — e.g., DLP egress scanning would have flagged the mass *query*
> volume even faster than a session-count Sigma rule reading logs after the fact; CMK/BYOK would not have
> stopped the read, but would have limited what a *later* storage-layer compromise could decrypt.

---

## Prove the control (your finish line)

Three assertions, watched — not just asserted:

> 1. **The label-based deny fires.** `analyst` reading a `restricted` record: `allow: false`,
>    **`deny: true`**.
> 2. **Fail-closed, proven by breaking it.** The unlabeled record (`rec-004`) resolves to
>    `effective_classification: "restricted"` — and with the default line changed to `"public"`, you
>    **watched** `analyst`'s read of it flip to `allow: true`. Restoring the line restores the deny.
> 3. **The exfil rule fires on the burst, stays silent on the normal session.** `sess_D2` (8 restricted
>    reads, one 2 AM session) produces exactly 8 `[HIT]` lines; `sess_D1` (`dpatel`'s 3 ordinary restricted
>    reads) produces none.

Run `make check` and confirm all four checks report `PASS`. **The proof is the pair in #2** — a policy
that only ever shows you the *fixed* behavior never demonstrated it fails closed; you have to see it fail
*open* first.

---

## Recall check — close the doc, answer from memory (3 min)

1. Which single line in the Rego policy makes an unlabeled record resolve to `restricted` instead of
   `public` — and what did you observe when you (temporarily) changed it?
2. Why does querying `deny` prove more than querying `allow` and finding it `false`?
3. `dpatel`'s 11 restricted reads across the log are *all* individually authorized by OPA. What tool
   catches the 8 that matter, and on what dimension does it key that OPA never looks at?
4. Name one control from Step 5 that would have caught the Snowflake-style pattern *before* the data left,
   not just detected it afterward in a log.

Missed one? Re-run the step that built it, or pull the
[module's label-based authorization section](README.md#label-based-authorization-the-same-opa-a-new-input) —
then re-answer.

---

## Deliverables

- **`data/policies/data-classification.rego`** — the label-based policy, `default allow := false`,
  `default effective_classification := "restricted"` intact (restored after Step 3).
- **`data/policies/data-classification_test.rego`** — the passing test suite, `opa test` green.
- **`fail-closed-proof.md`** — the one-line record from Step 3: what `effective_classification` and
  `allow` returned with the default line broken, and confirmation they returned to the safe values after
  the fix.
- **`examples/zt-bulk-restricted-read.yml`** — your tuned rule (restored to `> 5` after Step 4), plus a
  one-paragraph note on what `> 10` and `> 2` each got wrong.
- **`data-controls-design.md`** — the Step 5 write-up: CASB / DLP-egress / tokenization / CMK-BYOK / data
  residency mapped to gaps neither engine in this lab closes, tied to the Snowflake case, labelled
  *assessed from a design*.

*Lab artifacts you didn't change — the seeded `data/records.json`, `data/access-logs.jsonl` — stay
committed as shipped; don't regenerate them. The `git history` on the policy and the rule is the audit
trail for who changed the classification logic and when.*

## Automate & own it

**Required.** `check-data.sh` is the regression gate for this module — it asserts (1) the label-based
deny fires for a non-privileged role on restricted data, (2) the unlabeled record resolves to
`"restricted"` and is denied (fail-closed), (3) a privileged role is still allowed (this isn't
deny-everything), and (4) the bulk-read Sigma rule fires on `sess_D2` and stays silent on `sess_D1`.

Run it, watch it pass:

```bash
make check     # or: bash check-data.sh
```

Then **prove it both ways**, the same discipline as Module 08's `gate.sh`: re-plant the Step 3 bug
(`default effective_classification := "public"`) and re-run `make check` — check #2 must go **RED**.
Restore the fix and confirm **GREEN** again. Have a model draft the `docker compose run` / `grep`
plumbing if you like; **you verify** it fails for the *right* reason (the missing deny), not an unrelated
parse error, and that it fails **closed** — a script that silently exits 0 when a `docker compose` call
errors is worse than no gate at all.

## Definition of done (`data-pillar` ✅)

- [ ] `make demo` shows all five OPA decisions from Part 1 and exactly 8 `[HIT]` lines (`sess_D2`) from
  Part 2.
- [ ] You **watched** fail-closed break and recover: the unlabeled record read as `public`/`allow: true`
  with the default line changed, and back to `restricted`/`deny: true` restored — captured in
  `fail-closed-proof.md`.
- [ ] `make test` is green over `data/policies/`.
- [ ] You tuned the Sigma threshold both directions (`> 10` misses the burst, `> 2` flags normal work) and
  can explain why `> 5` is the defensible choice, not an arbitrary one.
- [ ] `make check` passes all four assertions; re-planting the Step 3 bug turns check #2 **RED**, and
  restoring the fix turns it green again.
- [ ] `data-controls-design.md` maps CASB / DLP-egress / tokenization / CMK-BYOK / data residency to
  specific gaps, tied to the Snowflake case, labelled assessed-from-design.
- [ ] You can explain all seven flight-card facts cold, especially #2 and #4.

## Connects forward

This module is built entirely from two engines you already own: **Module 08's OPA** now decides on a
new input (the record's classification, not just the requester's role), and **Module 09's Sigma /
`detect.py`** now keys on a new signal (restricted-read volume per session, not geography). Nothing here
is a new tool — it's the same judgment-as-code and detection-as-code disciplines pointed at the pillar the
rest of the track left open.

It also closes the set the track's capstone was judged against. The capstone (Modules 10–12's project)
proves every request was authenticated and authorized — but its audit trail says nothing about *what* was
authorized. Feed this module's classification-aware Rego into the capstone's policy, and its access log
through `zt-bulk-restricted-read.yml`, and the capstone's proof finally covers the fifth pillar too:
identity → device → network → workload → **data**, the full NIST SP 800-207 set an enterprise buyer
expects to see closed end to end.

## Marketable proof

> "I make data classification an access-control input, not metadata: I write OPA/Rego policy that
> authorizes by role × classification and **fails closed on a missing or unrecognized label** — I can
> show it break open and recover, not just assert it. I write a Sigma detection that catches
> **bulk-restricted-data reads as a session-volume signal**, distinct from identity or geography, tuned
> against both a too-loose and a too-tight threshold. And I can map the CASB/DLP/tokenization/CMK/
> data-residency controls a production data-loss-prevention program layers on top — honestly labelled as
> assessed, not stood up — the last of the five Zero Trust pillars closed."

## Stretch

- **Impossible-volume, not just impossible-travel.** Extend the held-out idea from Module 09: build a
  small labelled corpus of session/read-count pairs (a few genuine bulk-report jobs, a few real
  compromises) and score `zt-bulk-restricted-read.yml`'s precision/recall the way Module 09's `eval.py`
  scores the geo-rule — is a flat count threshold enough, or do you need a rate (reads per minute) too?
- **Wire the two engines together.** Extend `data-classification.rego` to accept a `session_read_count`
  input field and add a `deny` when a *single* request arrives already flagged as part of a bulk pattern —
  the PDP consuming the detection's output, closing the loop from "detect after the fact" to "deny the
  next one in real time."
- **Field-level, not record-level.** Real restricted records are rarely restricted end-to-end — a support
  ticket might be `internal` except for one embedded SSN. Sketch (don't build) what a field-level
  classification scheme would need from the Rego input shape, and name the tokenization control from
  Step 5 that makes it tractable at scale.
- **Map to ATT&CK.** Tie the bulk-read detection to **T1530** (Data from Cloud Storage — the read) and
  **T1567** (Exfiltration Over Web Service — the move-out), and write one sentence on which lab artifact
  is the control for each.
