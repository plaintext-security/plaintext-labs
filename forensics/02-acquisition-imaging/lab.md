# Lab 02 — Acquisition & Imaging

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/02-acquisition-imaging
make up        # build and start the dc3dd container
make demo      # run the worked imaging example (creates a 1MB source, images it, verifies)
make shell     # drop into the container to work interactively
make down      # stop when done
```

The container includes `dc3dd`. No large binary files are committed — the synthetic source device is
created at runtime as a 1MB sparse file inside the container (a tiny **fallback** so the worked
`make demo` runs with no network).

**Real evidence (primary artifact).** Image a *real* device instead of the synthetic 1MB file:
this lab is anchored to the **Digital Corpora M57-Patents** scenario — the first four weeks
(Nov 13–Dec 12 2009) of the fictional-but-real-public M57 Patents company, an outsourced
patent-search firm whose investigations include data exfiltration and illegal activity. It is a
genuine, citable public forensic corpus (Garfinkel et al.; digitalcorpora.org). Run
`make fetch-data` to download a real M57 USB image, then image *that* with `dc3dd` and verify it.

- Dataset root: <https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/>
- USB images (smallest suitable for imaging practice): <https://downloads.digitalcorpora.org/corpora/scenarios/2009-m57-patents/usb/>

See `PROVENANCE.md` in this directory.

> Fetching and hash validation are **deferred to runner-validation** — `make fetch-data` is wired
> but not yet executed here.

> Everything runs locally in Docker against files you own (or the freely licensed M57 corpus). No
> external targets, no authorization needed.

## Scenario
An endpoint at the affected organization (`BEACHHEAD-WS01`) was flagged by the EDR at 02:17 UTC —
anomalous outbound connection from a finance workstation. This mirrors the real **Lunar Spider**
intrusion documented by The DFIR Report, where a single click on a malicious `Form_W-9.js` led to a
near-two-month compromise and Rclone exfiltration (tool renamed `sihosts.exe`). Before the machine
is powered down, the IR lead asks you to **capture a memory image** (conceptual walkthrough) and
**demonstrate disk imaging on a test device** (the M57 USB image, or the synthetic fallback) using
`dc3dd` with inline hash verification. You need to prove the image matches the source before passing
it to the disk analyst.

> Only acquire and image systems you own or have explicit written authorization to examine. Never run acquisition tools against production systems without written approval and a documented chain of custody.

## Do

1. [ ] **Understand the container's imaging environment.**
   Run `make shell` and explore: where is `dc3dd` installed? What does `dc3dd --help` show you? What version is installed? Record the version in your notes — tool version is part of chain of custody.

2. [ ] **Create the source "device" and image it.**
   Inside the container (or via `make demo`), the lab creates a 1MB sparse file representing a small disk device, then images it with `dc3dd`:
   ```bash
   # Create the synthetic source (done by make demo)
   dd if=/dev/urandom of=/tmp/source.img bs=1M count=1

   # Image it with dc3dd, computing SHA-256 inline
   dc3dd if=/tmp/source.img of=/tmp/forensic-image.img hash=sha256 log=/tmp/acquisition.log

   # Inspect the log
   cat /tmp/acquisition.log
   ```
   What does the log report for the hash, the byte count, and the completion status? Note all three.

3. [ ] **Verify the image matches the source.**
   Compute `sha256sum` on both the source and the image:
   ```bash
   sha256sum /tmp/source.img /tmp/forensic-image.img
   ```
   The hashes must match. Do they? What would a mismatch tell you?
   Compare both hashes to the `dc3dd` log — all three values must agree.

4. [ ] **Simulate a write-block violation.**
   Mount the source image as a loop device inside the container and check whether any timestamps changed:
   ```bash
   losetup /dev/loop9 /tmp/source.img
   stat /tmp/source.img   # note atime/mtime
   losetup -d /dev/loop9
   ```
   Does even attaching a loop device change anything? Re-hash the source and confirm integrity. This illustrates why write-blocking matters even for "read-only" operations.

5. [ ] **Produce a case note.**
   Write `acquisition-notes.md` with:
   - Tool: `dc3dd` version X
   - Source: `/tmp/source.img` (synthetic 1MB test device)
   - Image: `/tmp/forensic-image.img`
   - SHA-256 of source: (value)
   - SHA-256 of image: (value — must match)
   - Acquisition start time (UTC)
   - Acquisition end time (UTC)
   - Write block method: (loop device, read-only mount, or hardware — note which applied)
   - Integrity verdict: VERIFIED / FAILED

6. [ ] **Memory acquisition walkthrough (conceptual).**
   You won't run a real memory dump (the lab is a container, not a live host), but write a short paragraph in `acquisition-notes.md` answering: If this were a live Linux host, how would you run `avml` to capture memory? What flags would you use? Where would you store the output, and why not on the suspect machine's own filesystem?

## Success criteria — you're done when
- [ ] `dc3dd` log exists and reports a SHA-256 hash.
- [ ] `sha256sum` of source and image match — and match the `dc3dd` log.
- [ ] `acquisition-notes.md` is complete with all required fields.
- [ ] You can explain what a hash mismatch between source and image would indicate.
- [ ] The memory acquisition paragraph correctly names `avml`, output location considerations, and why not to write to the suspect drive.

## Deliverables
Commit `acquisition-notes.md` to your fork. Do **not** commit `/tmp/source.img`, `/tmp/forensic-image.img`, or `/tmp/acquisition.log` — generated artifacts stay out of the repo.

## Automate & own it
**Required.** Write a shell script `acquire.sh` that:
1. Takes two arguments: source device/file and output directory.
2. Creates the output directory if it doesn't exist.
3. Runs `dc3dd` with SHA-256 hashing and logging to the output directory.
4. Re-hashes both source and image and prints a PASS/FAIL verdict.
5. Appends a timestamped summary line to an `evidence-log.txt` in the output directory.

Have a model draft the script; **read every line** and test it with the container before trusting it. This is the automation move for acquisition: a single reusable tool you hand off to the next responder with confidence.

## AI acceleration
Use a model to draft the `acquire.sh` script and the memory acquisition checklist. Ask it: "Given a live Linux host suspected of compromise with active malware, what is the correct acquisition order and why?" — then validate each answer against RFC 3227 and NIST SP 800-86 before treating it as authoritative.

## Connects forward
The verified image you'd produce here is the input to Module 03 (file system carving — you'll parse the filesystem from the raw image) and Module 07 (timeline analysis — plaso ingests the image to build the timeline).

## Marketable proof
> "I perform forensic disk and memory acquisition — sector-by-sector imaging with `dc3dd`, inline hash verification, and a documented chain of custody — in a way that holds up to scrutiny."

## Stretch
- Research E01 format: install `libewf` in the container and try `ewfacquire` on the test source. Compare the E01 output to the raw image — what metadata does E01 carry that a raw image doesn't?
- Look up WinPmem and DumpIt for Windows memory acquisition. How do they differ from `avml`? When would you use each?
