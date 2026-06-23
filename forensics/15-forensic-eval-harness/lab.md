# Lab 15 — Forensic Eval Harness: Proving a Detection Rule on a Held-Out Corpus

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment status:** the Docker environment for this lab is **to be built and validated**.
> The directory `plaintext-labs/forensics/15-forensic-eval-harness/` (a `docker-compose.yml`, a
> small bundled `data/` corpus of labelled benign/malicious artifacts, `scripts/eval.py`, and a
> `Makefile` with `up`/`down`/`reset`/`demo`) is not yet committed. The instructions below define
> the target shape; the lab is not "done" until `make up && make demo && make down` is green on a
> clean Linux runner and this note is removed.

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/15-forensic-eval-harness
make up && make demo
```

**Requirements:** Docker. ~512 MB RAM. **No network** — the eval runs your Module 11/12 detectors
over a *committed, labelled* corpus, so the whole lab is deterministic and runs offline, in CI too.
Python plus a YARA binary in the image; the timestomp half uses bundled file-metadata fixtures so no
real NTFS image is required.

`make demo` scores a **good** detector (the gate passes), then a **regressed** one — a YARA rule
loosened to match a benign string, and a timestamp-divergence threshold set so low it trips on
legitimate files (the gate fails) — and prints a verdict confirming the gate is green on the good
rule and red on the regression. That contrast is the whole lesson.

## Scenario

You wrote two detectors earlier in the track: a `$SI`/`$FN` timestomp detector (Module 11) and a YARA
rule for the Meridian dropper (Module 12). Both fired on the sample that prompted them. Now your lead
is about to run them across a 200,000-file enterprise disk image and asks the question you cannot answer
with adjectives: *do they actually discriminate malicious from benign — and how will we know the day a
rule edit silently blinds them?* Your job is to stop trusting the single-sample success: build a
**held-out** labelled corpus, choose a **metric** and defend it, score the detectors into a **scorecard**,
and wire a **CI regression gate** that fails when precision or recall drops.

> Everything runs locally against a committed corpus. No external targets, no live malware execution
> (PE samples are inert fixtures / hashes), no authorization needed.

## Do

1. [ ] **Read the held-out corpus, and understand *why* it's held out.** The bundled corpus has two
   halves: file-metadata records labelled timestomped vs. legitimately-modified, and PE feature records
   labelled malicious vs. benign — each with an answer key in `data/labels.json`. Confirm it is **separate
   from the samples Modules 11/12 were authored against**, and that it contains deliberate **near-misses**:
   a benign software installer that rewrites its own timestamps, a backup script that `touch -r`s files, a
   packed-but-legitimate binary. Skim three malicious and three benign items and confirm you could not
   separate them with a single naive check — that's the point: coverage of the hard cases, not just *more*.

2. [ ] **Run your detector over the corpus → recorded results.** `make detect` runs the Module-11 timestomp
   detector and the Module-12 YARA rule over every item and writes per-file verdicts. The detectors here are
   honest stand-ins so the loop runs offline; in real use you drop in *your* rules from Modules 11/12 — the
   corpus, eval, and gate are unchanged. Confirm you get a per-file verdict file, not a vibe.

3. [ ] **Score it and read the metric off the scorecard.** `make eval` prints the confusion matrix and
   **precision, recall, F1, FP-rate** for each detector, plus accuracy. Find the line marked *the metric that
   matters* and write, in one sentence per rule, **which error you can least afford and why** — and why
   accuracy alone is dangerous on this mostly-benign corpus (prove it: note that a "flag nothing" detector
   scores high accuracy and zero recall).

4. [ ] **Decide the gate per rule, deliberately.** Argue in `eval-report.md`: the timestomp detector is a
   *hunting* rule (favour recall — don't miss a hidden host), the YARA rule feeds *auto-triage* (favour
   precision — don't drown the queue). Set a defensible floor for each and justify it against the cost of the
   other error you're accepting.

5. [ ] **Watch the gate pass on good and FAIL on a regression — the core lesson.** `make demo` runs the gate
   on the good detectors (passes, exit 0) and on `regressed/` (fails, exit 1): a YARA rule loosened to match a
   benign string (precision collapses) and a divergence threshold dropped so low legitimate files trip it
   (FP-rate explodes). Open the regressed rule and confirm you can see *why* the scorecard went red. The
   green/red contrast is what lets a team edit a rule without blinding it.

6. [ ] **Tune and watch the tradeoff move.** Loosen the timestomp threshold to catch one more "variant" and
   re-score: confirm recall ticks up while precision drops as benign files start tripping. Pick the operating
   point deliberately and record the knee in `eval-report.md`.

7. [ ] **Expand the corpus with an adversarial benign case.** Add one *new* benign file that legitimately
   rewrites timestamps (label it yourself), re-run, and confirm whether your chosen threshold now produces a
   false positive. Note in the report what that tells you about the rule.

## Success criteria — you're done when

- [ ] `make demo` runs offline and ends with `PASS: gate is GREEN on the good detectors and RED on the regression`.
- [ ] `make eval` prints a confusion matrix + precision/recall/F1/FP-rate for both the timestomp and YARA detectors.
- [ ] You can state, in writing, which error each rule can least afford, the gate floor you chose, and why accuracy misleads on this corpus.
- [ ] You've seen the gate fail on the loosened YARA rule and on the over-sensitive divergence threshold.
- [ ] `eval-report.md` is filled in: per-rule metric + threshold + justification, the precision/recall knee, and the adversarial-benign result.

## Deliverables

Commit to your portfolio repo:
- `eval.py` (with any metric/gate change you made) + the held-out corpus + `eval-report.md`.

The eval-as-code **is** the artifact: a held-out labelled corpus, a precision/recall scorecard, and a gate that
fails on regression. Do **not** commit generated per-file verdicts or metric dumps — they're gitignored; the
corpus and the eval regenerate them, and never commit live malware binaries (the PE half is inert fixtures/hashes).

## Automate & own it

**Required.** Wire the gate into CI so a rule regression *cannot merge*. Add a `.github/workflows/detector-eval.yml`
(in your own portfolio repo) that runs, on every PR, your `eval.py` over the committed corpus with a precision floor
on the YARA rule and a recall floor on the timestomp detector. Have a model draft the workflow YAML — it's boilerplate.
**You own three things it will get wrong:** (1) the gate must **fail closed** — if the eval errors, a file won't parse,
or a metric is missing, the build fails, it does not silently pass (verify by feeding a corrupt fixture and confirming
a non-zero exit); (2) the threshold *direction* per rule (a precision floor for one, a recall floor for the other);
(3) that what CI scores is the *held-out* corpus, never the samples the rules were authored from. Commit the workflow
and a log of it going red on a planted (loosened) rule.

## AI acceleration

Have a model **expand the corpus with adversarial items** — benign files crafted to look timestomped (installers,
backup jobs), and packed-but-legitimate binaries that a naive YARA rule would flag — then **label each yourself and
verify it against what the file actually does**. A model labelling its own corpus is exactly the contamination this
module warns about; you generate candidates, you own the ground truth. Then ask a frontier model to critique your
metric choice ("I'm gating the dropper rule on precision ≥ 0.95 for auto-triage — what am I missing?") and weigh its
answer against the FP-rate cost you measured.

## Connects forward

This is the measurement layer Modules 11 and 12 were missing. **Module 11's** `$SI`/`$FN` detector and **Module 12's**
YARA rule swap "I wrote a rule" for "I proved a rule on a corpus I didn't author, gated so it can't silently regress."
Module 16 reuses the same instinct against AI output: a rule needs a held-out corpus; an AI summary needs an artifact
trace.

## Marketable proof

> "I built an eval harness for forensic detection rules — a held-out, labelled benign/malicious corpus, a
> precision/recall scorecard with the metric chosen for each rule's job, and a CI regression gate that fails the
> build when a rule edit silently degrades detection. I can prove my detectors discriminate, not just claim they
> caught the one sample I wrote them from."

## Stretch

- Add a **precision/recall curve**: sweep the timestamp-divergence threshold and print recall vs. FP-rate, then mark
  the operating point you chose and defend it.
- Run your YARA rule through `yarGen`'s goodware-subtraction idea by hand: identify a string in your rule that also
  appears in benign software in the corpus, add a `$fp*` filter, and show the precision improvement on the scorecard.
