# Lab 03 — File Systems & Carving

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/03-file-systems-carving
make up        # build the SleuthKit + foremost container
make demo      # run the worked example: parse the FAT32 image, recover deleted file
make shell     # drop in to explore interactively
make down      # stop when done
```

The container includes `sleuthkit` and `foremost`. `data/disk.img` is a committed 2MB FAT32
image with a planted "deleted" file — small enough to commit (< 2MB).

> Everything runs locally against a bundled image you own. No external targets, no authorization needed.

## Scenario
The Meridian IR team recovered a USB drive from the suspect's workstation. Initial triage shows a FAT32 filesystem with what appears to be normal files — but the analyst suspects important files were deleted before the drive was seized. Your task is to parse the filesystem metadata, enumerate deleted entries, and recover whatever was removed. The drive image is `data/disk.img`.

> Only examine evidence you are authorised to handle. In a real case, this image would carry a hash-verified chain of custody from Module 01.

## Do

1. [ ] **Identify the filesystem.**
   Run `fsstat data/disk.img` and record: filesystem type, cluster size, root directory inode, and total sectors. These are the basic parameters you'll reference throughout the analysis.
   *Hint:* `fsstat` is the SleuthKit tool that reads the superblock/BPB and reports volume-level metadata.

2. [ ] **List all files, including deleted ones.**
   Run `fls -r -d data/disk.img` to list the entire directory tree, flagging deleted entries.
   Which files are marked with `*`? Note their inode numbers — you'll need them for recovery.
   *Hint:* `-r` is recursive; `-d` lists deleted entries; `*` in the output flags a deleted entry.

3. [ ] **Examine a deleted file's metadata.**
   Pick the deleted file's inode number from step 2 and run `istat data/disk.img <inode>`.
   What does the output tell you about the file? Note: allocated/unallocated status, data units (cluster numbers), and any timestamps present.

4. [ ] **Recover the deleted file's content.**
   Use `icat` to extract the content of the deleted inode to a recovered file:
   ```bash
   icat data/disk.img <inode> > /tmp/recovered-file
   ```
   What is in the recovered file? Does the content make sense as evidence in the Meridian scenario?

5. [ ] **Carve unallocated space with foremost.**
   Run `foremost` against the disk image to find any additional content in unallocated space:
   ```bash
   foremost -t all -i data/disk.img -o /tmp/foremost-out/
   ```
   What file types did `foremost` recover? Check `/tmp/foremost-out/audit.txt` for a summary.
   Are any recovered files different from what `fls` found? This illustrates the difference between inode-based recovery and carving.

6. [ ] **Document your findings.**
   Write `findings.md` with:
   - `fsstat` summary (filesystem type, cluster size)
   - List of deleted files found by `fls` with their inode numbers
   - Content of recovered file (or a description)
   - What `foremost` recovered and how it compared to `fls`
   - Short paragraph: why can `icat` recover this content? What conditions would make recovery impossible?

## Success criteria — you're done when
- [ ] `fsstat` output is documented (filesystem type, cluster size, volume parameters).
- [ ] At least one deleted file was found with `fls -d`.
- [ ] `icat` successfully extracted the deleted file's content.
- [ ] `foremost` was run and its output reviewed.
- [ ] `findings.md` explains why recovery was possible and what would prevent it.

## Deliverables
Commit `findings.md` to your fork. Do **not** commit `/tmp/recovered-file` or `/tmp/foremost-out/` — generated output stays out of the repo.

## Automate & own it
**Required.** Write a Python or shell script `carve-report.sh` that:
1. Takes a disk image path as argument.
2. Runs `fls -r -d` and parses the output to list only deleted entries.
3. For each deleted entry, runs `icat` to extract the content and saves it to an output directory named by inode.
4. Produces a Markdown summary report of all recovered files.

Have a model draft the script; **read every line** and test it against `data/disk.img` before committing. This is the automation move for disk triage: you'd run this against every seized image to get a first pass of deleted-file candidates before manual review.

## AI acceleration
Feed your `fls` output to a model and ask it to explain each line, identify which entries are directories vs. files, and flag which inodes might be most relevant to a data exfiltration investigation. Use it to draft the foremost configuration entry for a new file type (e.g., a custom log format). Verify every inode number and offset it names against the actual tool output — models confabulate specific numeric values.

## Connects forward
The filesystem layer you work here is the foundation for Module 04 (Windows artifacts live in NTFS structures — `$MFT`, `$LogFile`, prefetch files) and Module 07 (plaso ingests disk images and parses filesystem timestamps into the super-timeline).

## Marketable proof
> "I recover deleted files from disk images using SleuthKit's inode-level tools and foremost carving — navigating the filesystem layer model to find what attackers thought they erased."

## Stretch
- Research the `$UsnJrnl` on NTFS: what does it record, and how would you extract it with SleuthKit or `MFTECmd`?
- Try `tsk_recover` on the disk image: how does it differ from your manual `icat` approach? What does it miss?
