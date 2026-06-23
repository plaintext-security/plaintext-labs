# Lab 11 — Host & Boot Integrity with AIDE

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Everything runs
locally in Docker: a small Debian "host" with **AIDE** installed, a watched application tree, and
scripts to baseline it, tamper with it, and prove the tamper is caught. No cloud account, no VM.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/11-host-boot-integrity
make up           # build the host + build the known-good AIDE baseline
make check        # assert: a fresh baseline reports CLEAN (no changes)
make tamper       # plant 3 changes: modified binary, new SUID-root file, dropped cron
make check        # assert: AIDE flags all three planted changes
make demo         # the full walkthrough (clean -> tamper -> detect)
make down         # stop when done
```

The container plays the role of *a host you just provisioned*: `make up` snapshots its filesystem
into an AIDE baseline (the "known-good"), and every later `aide --check` measures the live host
against that snapshot. The watched policy, baseline script, and tamper script live under `data/` so
you can edit them and re-baseline.

> Everything runs locally against a container you own. No external targets, no authorization needed.
> **First run note — pending validation:** this environment is new and has **not yet been run
> end-to-end on this machine** (Docker was unavailable when it was authored), so treat the first
> `make up`/`make demo` as the validation pass. The shell scripts are syntax-checked (`bash -n`) and
> the compose file is valid, but likely first-run friction points are: (a) AIDE's exit code is a
> *bitfield* — `--check` returns non-zero when it finds differences, which is the **expected**
> success state after `make tamper` (the check script keys on the report text, not the raw code, to
> stay version-robust); (b) the Debian `aide` package's default `/etc/aide/aide.conf` is *not* used
> here — the lab passes `--config=/lab/data/aide.conf` explicitly, so ignore any packaged config; and
> (c) the baseline DB lands in `/var/lib/aide` *inside the container* and is wiped by `make reset` —
> that's intentional (see step 5 on why a real baseline lives off-box). If `make up` snags, the moving
> parts are `data/setup.sh` (the `--init` then promote-the-DB step) and `data/aide.conf` (the watched
> paths and attribute groups).

## Scenario

Meridian Financial has hardened its Linux fleet to a CIS baseline (Module 03), pushed it as code
(Module 06), and stood up telemetry (Module 05). Then IR gets a tip: *one host may have been touched
during last month's incident.* Hardening tells you how the box was **configured**; it says nothing
about what **changed** since. You'll give Meridian the missing answer — a file-integrity baseline that
can prove, on demand, whether a host still matches its known-good state — and then play the attacker:
plant a trojaned binary, a SUID-root backdoor, and a persistence cron, and watch the baseline catch
every one. Finally you'll confront the control's own weak point — the baseline database — and reason
about the boot chain that runs *before* any file checker exists.

## Do

### Part 1: Build and trust a known-good baseline
1. [ ] **Bring it up and read what got watched.** `make up`, then open `data/aide.conf`. Note the
   two things a policy must get right: the **watched paths** (`/srv/app`, `/etc/cron.d`) and the
   **attribute group** (`p+u+g+n+s+b+m+c+sha256`) — content hash *plus* permission/owner/inode
   metadata, so a file made SUID-root *in place* is caught even if its bytes don't change. Why is
   watching the cron *directory* (not just files in it) what catches an *added* job?

2. [ ] **Confirm the baseline is clean.** `make check` (or `make check-clean`). With no tamper yet,
   `aide --check` must report **no differences**. This is the contract: green here means "the live
   host matches the snapshot `make up` took." Read `data/setup.sh` — where does the baseline DB land,
   and what does the script say about protecting it?

### Part 2: Plant a tamper and prove detection
3. [ ] **Play the attacker.** `make tamper` runs `data/tamper.sh`, which establishes a foothold three
   classic ways: (1) **trojans the app binary** (`/srv/app/bin/meridian` — content changes), (2)
   **plants a SUID-root binary** (`/srv/app/bin/.helper`, mode `4755`, owner root — a privilege-escalation
   primitive), and (3) **drops a persistence cron** (`/etc/cron.d/meridian-update`). Read the script;
   each tamper maps to a real ATT&CK technique (T1554 / T1548.001 / T1053.003).

4. [ ] **Catch all three.** `make check` again. AIDE re-fingerprints the watched tree, diffs against
   the baseline, and reports every change with *which* attributes moved (a changed `sha256` on the
   binary; a new `f` entry with `SUID` set; an added file under `/etc/cron.d`). Confirm all three
   planted paths appear. In your write-up, note for each: what attribute revealed it, and what an
   attacker would have had to also do to hide it from this policy.

### Part 3: Protect the control, then re-baseline
5. [ ] **Attack the baseline itself (the real lesson).** With the host still tampered, *overwrite the
   baseline* the way an attacker who rooted the box would: from the `make shell`, re-run
   `aide --config=/lab/data/aide.conf --init && mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db`,
   then `make check` — it now reports **clean**, because the baseline now *includes* the tamper. This
   is the core point: **a FIM whose database the attacker can rewrite is theater.** In your write-up,
   state where the baseline DB (and the AIDE binary and config) *should* live so this can't happen —
   read-only/offline media, or a separate host that pulls and verifies — and how you'd verify the DB's
   own integrity (a hash you keep off-box) before trusting a check.

6. [ ] **Re-baseline cleanly.** `make reset && make up` to rebuild from a clean image, then
   `make check` (clean) → `make tamper` → `make check` (detects) to confirm the full loop reproduces.
   This is the operational cycle: after an *approved* change (a package update), you re-`--init` and
   move the new DB into place so legitimate changes don't generate noise — the discipline is knowing
   *which* changes are approved before you re-baseline over them.

### Part 4: Boot integrity (prose + optional VM stretch — does not run in the container)
7. [ ] **Reason about the boundary AIDE can't see.** A container can't run Secure Boot, a TPM, or
   FDE, so this step is analysis (and an optional VM build below). In your write-up, place the three
   boot-chain controls precisely: **Secure Boot** *prevents* (UEFI signature-verifies the bootloader
   and kernel, refusing anything unsigned/tampered); **measured boot** *detects* (each stage hashes
   the next and extends a TPM **PCR**, building a tamper-evident log you can **attest** against
   known-good values); **FDE/LUKS** *protects at rest* (confidentiality if the disk is stolen, not
   detection). State plainly: AIDE is blind to everything before the filesystem mounts — *which* of
   these covers that window, and why **sealing a LUKS key to a TPM PCR state** ties disk encryption to
   boot integrity (the volume only unlocks if the measured boot chain is the expected one).

## Success criteria — you're done when
- [ ] `make up` builds a baseline and `make check` reports the fresh host **clean** (no differences).
- [ ] `make tamper` plants the three changes and `make check` flags **all three** — the modified
  binary, the new SUID-root file, and the dropped cron — naming the attribute that revealed each.
- [ ] You demonstrated the **baseline-rewrite** failure (step 5) and documented where the DB/binary/config
  must live so a compromised host can't defeat the check.
- [ ] `make reset && make up` reproduces the full clean → tamper → detect loop.
- [ ] `findings.md` covers the boot-chain analysis: Secure Boot (prevent) vs. measured boot/TPM PCRs
  (detect) vs. LUKS FDE (protect at rest), and what FIM cannot see.

## Deliverables
`findings.md` — the integrity write-up: the watched policy and *why* those paths/attributes; the clean
baseline; the three tampers and the AIDE attribute that caught each; the baseline-rewrite demonstration
and where the DB belongs; and the boot-integrity placement (Secure Boot / measured boot / FDE). Commit
it. **Never commit the AIDE database, `aide.db*`, or raw reports** — they're in `.gitignore`; reference
them in the prose.

## Automate & own it
**Required.** Turn the manual check into a small **integrity-monitor wrapper** you'd actually schedule:
a script (`integrity-check.sh`) that runs `aide --check`, parses the report into a structured summary
(added / removed / changed counts, and the *paths* of any new SUID files or new `/etc/cron.d` entries —
the high-signal indicators), and **exits non-zero with a clear, greppable line** when anything in the
watched-immutable set changed, so cron or a CI job can alarm on it. Have a model draft the report
parsing and the JSON/line summary; **you own two things it will get wrong** — the *allowlist* of
expected-changeable paths (don't let it silence a directory that also holds things you must watch), and
the **trust check on the DB itself** (verify the baseline's off-box hash before believing a "clean"
result). Commit it as `integrity-check.sh` alongside `findings.md`.

## AI acceleration
A model writes an `aide.conf` and parses an AIDE report fluently — use it to draft the watched policy,
suggest sensible excludes for `/var`, `/proc`, and `/tmp`, and triage a noisy diff into
"expected (package update)" vs. "suspicious (new SUID / modified `/etc/passwd` / unexpected cron)."
Where you own the judgment: the **excludes are a security decision** — ask it to quiet the noise and it
will cheerfully exclude a path that *also* contains things you must watch (the FIM version of an
over-broad firewall rule) — and, non-negotiable, the model **cannot tell you whether your baseline is
trustworthy**. It validates the config and reads the report without ever asking whether the DB it's
comparing against was itself tampered. AI drafts the config and explains the diff; you decide what's
watched, protect the baseline off-box, and prove the planted tamper is caught.

## Connects forward
This is the *state* counterpart to the *event* detection in **Module 05** (osquery telemetry) and
**Module 10** (Sigma rules): telemetry catches the attacker *acting*, FIM catches the *residue* they
left on disk — run both and a missed event still surfaces as a changed file. The baseline-rewrite
lesson is the same "protect the reference" discipline as **Module 17 — Data Protection & KMS** ("the
key policy is the off-switch") one layer down. And the boot-chain analysis (Secure Boot / measured
boot / TPM / LUKS) is the hardware root of trust the **capstone** assumes when it asks you to prove a
host's state holds from the silicon up.

## Marketable proof
> "I build AIDE file-integrity baselines, prove they catch planted persistence — a trojaned binary, a
> SUID-root backdoor, a malicious cron — and I treat the baseline database as the real control:
> off-box, hash-verified, re-baselined only over approved changes. I can place the boot-chain
> controls precisely — Secure Boot prevents, measured boot/TPM PCRs detect, LUKS protects at rest —
> and explain exactly what file integrity can and can't see."

## Stretch
- **Harden the policy to CIS shape.** Extend `aide.conf` toward a real benchmark slice: watch `/bin`,
  `/sbin`, `/usr/bin`, `/etc`, and audit the whole-filesystem SUID/SGID set, with `/var/log` watched
  only for permission/owner (not content). Re-baseline and confirm a system package update produces a
  *legible* (not overwhelming) diff — that's the tuning skill the job actually needs.
- **Boot integrity for real (VM lab).** On a UEFI VM you own (snapshot first), enable **Secure Boot**
  and confirm the running state (`mokutil --sb-state`); read the TPM PCRs (`tpm2_pcrread` or
  `/sys/class/tpm/tpm0/...`) and note which PCRs the firmware/bootloader/kernel extend; then **LUKS-encrypt**
  a spare volume with `cryptsetup luksFormat` and **seal its key to a PCR state** with `systemd-cryptenroll
  --tpm2-device=auto --tpm2-pcrs=7` so the volume auto-unlocks only when the boot chain is unchanged.
  Tamper the boot config and prove the seal refuses to release the key — measured boot, detection, end
  to end.
- **Off-box baseline.** Move the AIDE DB to a read-only mount (or a second container that pulls it),
  verify its hash before each check, and demonstrate that the step-5 baseline-rewrite attack now fails
  because the attacker can't reach the trusted copy.
