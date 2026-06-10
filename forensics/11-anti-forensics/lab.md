# Lab 11 — Anti-Forensics & Detecting It

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/11-anti-forensics
make up      # builds the Sleuth Kit container with the synthetic disk image
make demo    # runs fls + istat over disk.img and shows the timestamp discrepancy
make shell   # interactive shell for investigation
make down    # stop when done
```

The lab ships `data/disk.img` — a small FAT32/ext2 hybrid image (under 2MB) containing:
- A directory of "normal" files with coherent timestamps.
- A timestomped file: SI timestamps set to 2019, FN timestamps from 2024 — the attacker's
  manipulation left traces.
- A deleted file recoverable in unallocated space.

> All data is synthetic. No real incident artifacts are included.

## Scenario

The disk image was pulled from `WORKSTATION-04` during full acquisition (module 02 workflow).
The timeline (module 07) showed a suspicious gap: a file appears in the MFT but its timestamp
predates the workstation's deployment date. The attacker used a timestomper to make a dropped
binary look like a system file. Your task: prove the manipulation using NTFS attribute analysis.

> Only examine evidence you are authorised to handle. Forensic imaging of production systems
> requires prior approval and chain-of-custody documentation.

## Do

1. [ ] **`make demo`** — read the output. Find the file with the suspicious timestamp discrepancy.
   What are the SI Created and FN Created timestamps? How large is the gap?

2. [ ] **Run `fls` manually** inside `make shell` to list all files on the image:
   ```bash
   fls -r -l /data/disk.img
   ```
   Note the inode number of the suspicious file. (It will appear with an anomalous date compared
   to surrounding entries.)

3. [ ] **Run `istat`** on that inode to dump all NTFS attribute timestamps:
   ```bash
   istat /data/disk.img <inode_number>
   ```
   Record the full output. Which attribute timestamps diverge? By how much?

4. [ ] **Recover the deleted file.** Use `icat` to extract content from unallocated space:
   ```bash
   icat /data/disk.img <deleted_inode_number> > /tmp/recovered_file
   file /tmp/recovered_file
   md5sum /tmp/recovered_file
   ```
   What type of file was deleted? Is it recoverable? Note the MD5 hash.

5. [ ] **Run the Python detection script:**
   ```bash
   python3 /scripts/detect_timestomping.py /data/disk.img
   ```
   Does it flag the manipulated file? Does it produce any false positives on the benign files?
   Review the detection logic and identify one way the script could miss a sophisticated
   timestomper (e.g., if FN is also modified).

6. [ ] **Document the anti-forensics finding** in one paragraph: the file name, the SI timestamps,
   the FN timestamps, the delta, and your conclusion about whether this represents manipulation.
   Reference the `istat` attribute names (not just "Modified timestamp").

## Success criteria — you're done when

- [ ] You have the SI and FN timestamps for the manipulated file, documented by attribute name.
- [ ] You have the istat dump for the inode, attached or summarised in your finding.
- [ ] You have the MD5 hash of the recovered deleted file.
- [ ] Your one-paragraph finding cites the specific timestamp discrepancy and concludes on manipulation.
- [ ] You have identified one limitation of the `detect_timestomping.py` approach.

## Deliverables

Commit to your portfolio repo:
- `anti-forensics-finding.md` — your documented timestamp discrepancy finding with istat output excerpted.
- `detect_timestomping.py` — the detection script (reviewed and optionally improved from the lab version).

Do not commit `disk.img` — it is in the labs repo, not the prose repo.

## Automate & own it

**Required.** Extend `detect_timestomping.py` to also:
1. Flag any file whose SI Modified timestamp is earlier than its SI Created timestamp (physically
   impossible under normal Windows behaviour).
2. Flag any file whose SI timestamp falls outside the known deployment date range for the system
   under examination (pass the earliest and latest expected date as CLI arguments).
3. Output results as JSON for downstream processing (a SIEM ingest pipeline, for example).

Have a model draft the extensions; **test each new check against a benign disk image** (the one
shipped in the lab) before claiming it works. A detection that fires on every file is not a
detection — it's noise. Commit the extended script.

## AI acceleration

Feed the fls output (a file listing with timestamps) to a model and ask: "Are there any timestamp
anomalies in this listing that could indicate timestomping? Reference the specific fields and
values." Compare the model's answer to your istat analysis — the model may miss the SI/FN
distinction (since fls shows only one set of timestamps by default) but may catch clustering
anomalies (all files in a directory have round timestamps, suggesting a batch operation).

## Connects forward

Module 13 (IR Process) asks you to document the anti-forensics finding as part of the NIST
analysis phase. Module 14 (Reporting) requires you to express this finding at both technical and
executive levels — the istat dump is the technical support; the one-paragraph summary is the
executive sentence.

## Marketable proof

> "I detect timestomping by comparing NTFS Standard Information and File Name attribute
> timestamps using The Sleuth Kit, and I write Python scripts that automate the detection
> for triage across large disk images."

## Stretch

- Create a second disk image with a file where *both* SI and FN are manipulated — the harder
  case. What artifacts would you use to detect manipulation in that scenario? (Hint: look at the
  $LogFile and $MFT change timestamps, and the $UsnJrnl entry for the file.)
- Extend the detection script to parse $UsnJrnl records (using the `fsstat` output) and flag
  files where the USN journal entry date contradicts the SI timestamp.
