# Lab 01 — Forensic Fundamentals & Evidence Handling

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/01-forensic-fundamentals
make demo      # run the worked hashing + chain-of-custody example
```

No container is required for this module: `sha256sum`, `md5sum`, and `dc3dd` are used directly.
If `dc3dd` is not installed on your host, the Makefile will run it via Docker.

> Everything runs against files you own in `data/`. No external targets, no authorization needed.

## Scenario
A Meridian Financial security analyst has flagged two files recovered from a suspicious USB drive found on a finance floor workstation. Before any analysis begins, the IR lead hands you the task: **establish integrity and start the chain of custody.** The files are `data/evidence-sample.txt` and `data/evidence-sample.bin`. Your job is to hash them, document the results, and prove they haven't been altered before passing them to the next examiner.

> Only examine evidence you are authorised to handle. In a real investigation, evidence must be handled according to your organization's evidence-handling policy and applicable law.

## Do

1. [ ] **Compute hashes for both evidence files.**
   Run `sha256sum` and `md5sum` against `data/evidence-sample.txt` and `data/evidence-sample.bin`.
   Record the output exactly — hash, filename — in a file called `chain-of-custody.md`.
   *Hint:* `sha256sum data/evidence-sample.txt >> chain-of-custody.md`

2. [ ] **Verify the hashes a second time.**
   Re-run `sha256sum -c` (or manually compare) to prove the files haven't changed since step 1.
   What does a mismatch look like? Try appending a space to `evidence-sample.txt` and re-hashing — see the hash change, then restore the file and re-verify.

3. [ ] **Image a file with `dc3dd`.**
   Use `dc3dd` to copy `data/evidence-sample.bin` to `data/evidence-sample.bin.img`, computing the hash inline during the copy:
   ```bash
   dc3dd if=data/evidence-sample.bin of=data/evidence-sample.bin.img hash=sha256 log=data/dc3dd.log
   ```
   Open `data/dc3dd.log` and find the reported hash. Compare it to the `sha256sum` you computed in step 1 — they must match.
   *This is the forensic proof: the image was accurate at the moment of capture.*

4. [ ] **Document the chain of custody.**
   Add a chain-of-custody entry to `chain-of-custody.md` for each file. At minimum, each entry should include:
   - Filename and SHA-256 hash
   - Collection date/time (use `date -u` for UTC)
   - Collected by (your name/handle)
   - Storage location (e.g. `plaintext-labs/forensics/01-forensic-fundamentals/data/`)
   - Next custodian (e.g. "IR Lead — analysis phase")

5. [ ] **Explain the write-block principle.**
   In `chain-of-custody.md`, add a short paragraph: why would mounting the source USB drive without a write blocker — even read-only — potentially alter evidence? Name at least two metadata fields that could change.

## Success criteria — you're done when
- [ ] SHA-256 hashes for both evidence files are recorded in `chain-of-custody.md`.
- [ ] `dc3dd` log (`data/dc3dd.log`) exists and its reported hash matches the `sha256sum` output.
- [ ] Your `chain-of-custody.md` has a complete, timestamped entry for each file.
- [ ] You can explain why the two hashes (step 1 and step 3) must match, and what it would mean if they didn't.
- [ ] The write-block paragraph names at least two metadata fields that mounting can alter.

## Deliverables
Commit `chain-of-custody.md` to your fork. This is the portfolio artifact — it shows you know how to start a defensible investigation. Do **not** commit `data/dc3dd.log` (generated) or any modified copies of the evidence files.

## Automate & own it
**Required.** Write a small shell script `hash-evidence.sh` that:
1. Accepts a directory path as its argument.
2. Computes SHA-256 for every file in that directory.
3. Writes a timestamped, formatted evidence log to `evidence-log-<timestamp>.txt`.

Have a model draft the script; **you read every line** and confirm the output format is correct before trusting it. Commit `hash-evidence.sh` alongside `chain-of-custody.md`. This is the automation move for intake: never hash by hand when you're collecting twenty files under time pressure.

## AI acceleration
AI is useful for two things here: drafting the chain-of-custody template (ask it to produce a Markdown table with the required fields), and explaining edge cases ("what happens to MAC times if I mount an NTFS volume read-only on Linux?"). It is *not* a substitute for running the actual hash commands and recording the actual output — that step must be manual and verified.

## Connects forward
The hash-and-image discipline you establish here applies to every artifact you collect in the track: disk images in Module 02, memory samples in Module 06, and timeline inputs in Module 07. Chain of custody is the thread that ties the whole investigation together.

## Marketable proof
> "I establish forensic integrity before any analysis — hashing evidence with SHA-256, imaging with `dc3dd` for inline verification, and documenting a complete chain of custody from collection through handoff."

## Stretch
- Look up NIST's guidance on dual-hashing (MD5 + SHA-1 alongside SHA-256). When do courts or agencies still require the older algorithms, and why? Document your finding.
- Research hardware write blockers: name two commercial products, their approximate cost, and one scenario where a software write blocker (Linux `blockdev --setro`) would be legally risky.
