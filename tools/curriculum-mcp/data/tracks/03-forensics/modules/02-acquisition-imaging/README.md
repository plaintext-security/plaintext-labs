# Module 02 — Acquisition & Imaging

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *the only shot you get at the original evidence is the first one — take it cleanly.*

## Why this matters
Acquisition is the most time-sensitive and least reversible step in any forensic investigation. If you image a disk sector-perfectly with a verified hash, every subsequent analysis phase can work from that image indefinitely. If you skip the write block, run the wrong tool, or copy only the visible filesystem, you may destroy the very data your investigation depends on — and you can never go back to the original. Memory acquisition is even more time-critical: the moment a machine reboots or the user kills a process, that volatile state is gone. This module teaches you to capture evidence cleanly under pressure.

## Objective
Image a disk device sector-by-sector using `dc3dd`, verify the image with inline hash comparison, and understand the considerations for memory acquisition with `avml`; articulate the trade-offs between dead-box and live acquisition for a given scenario.

## The core idea
When you image a disk forensically, you are not copying files — you are copying *every bit on the physical medium*, from sector zero to the end. This matters because deleted files, slack space, unallocated clusters, and volume metadata all live outside what the filesystem presents to the OS. A file-level copy (`cp -r`) misses everything the OS considers "gone." A forensic tool like `dc3dd` reads the raw block device and writes every sector to the output image, reporting the hash as it goes. The image is a bit-for-bit clone, provably identical to the original.

**The discipline of dead-box versus live acquisition** is the first call you make on a real engagement. Dead-box (powered-off machine, hardware write blocker, image the drive) is the gold standard for non-volatile evidence: no running processes can modify timestamps, extend logs, or drop additional payloads during acquisition. The trade-off is everything in RAM disappears the moment power is cut — encryption keys, running process state, network socket tables, injected shellcode that never touched disk. Live acquisition (image the disk and capture memory *while the system runs*) preserves volatile artifacts but introduces risk: the running OS continues to write to disk, so the disk image you take is of a system in motion, not a frozen moment. Neither approach is universally correct; the right call depends on what your investigation needs most.

**Memory acquisition** is a separate discipline from disk imaging. Memory is a running snapshot of the entire system's state: every process's virtual address space, the OS kernel, device drivers, cached files, and whatever the malware running right now is doing. `avml` (Acquire Volatile Memory for Linux) is a kernel-level tool that produces a raw memory dump suitable for Volatility3 analysis. Windows equivalents include WinPmem and DumpIt. The challenge with memory acquisition is that the tool itself must be memory-resident to run, and on a live system the contents are changing as you capture — you get a consistent-enough snapshot, not a perfect freeze-frame. This is fine for investigation purposes; just document the acquisition time precisely.

The practical workflow on a modern IR engagement runs like this: for a suspected compromised host, you arrive with a forensic kit (write blockers, bootable forensic USB, `avml` or equivalent pre-staged), capture memory first (highest volatility), then image the disk with a write blocker in place if the machine is being imaged live, or boot to a forensic OS and image with the machine powered off. Every step is documented with timestamps, tool versions, and hash values in your case notes. A forensic acquisition that can't be reproduced in a court room is not forensic — it's a guess.

**Image formats** are worth understanding. Raw (`dd`-style) images are maximally compatible — every tool can read them — but large. E01 (Expert Witness Format) is the industry standard for disk images: compressed, split into segments, with built-in metadata including hashes and case information. `dc3dd` outputs raw; `ewfacquire` (from `libewf`) produces E01. For the purpose of this curriculum and the lab, raw images are fine — they keep the toolchain minimal and the pipeline transparent.

## Learn (~3.5 hrs)

**Disk acquisition (~1.5 hrs)**
- [The Forensics Wiki — Dd](https://forensicswiki.xyz/wiki/index.php?title=Dd) — explains the differences between `dd`, `dc3dd`, and `dcfldd`; short but precise.
- [libewf / ewfacquire man page](https://manpages.ubuntu.com/manpages/focal/man1/ewfacquire.1.html) — for when you need E01 output. Skim to understand the format options.

**Memory acquisition (~1 hr)**
- [Microsoft AVML on GitHub](https://github.com/microsoft/avml) — the tool's README and usage flags; read the "Usage" section to understand how it produces a usable memory image.
- [Memory Acquisition Techniques — SANS DFIR Cheat Sheet](https://www.sans.org/posters/memory-forensics-cheat-sheet/) — a one-page reference covering Windows and Linux tools side-by-side; a useful quick-reference for the field.

**Dead-box vs. live — the judgment call (~1 hr)**
- [NIST SP 800-86 § 3.1 — Evidence Prioritization and Volatile Data](https://csrc.nist.gov/pubs/sp/800/86/final) — the authoritative treatment of volatile-vs-non-volatile tradeoffs. Read section 3.1 specifically.
- [First Response — Chris Sanders & Jason Smith, Applied Network Security Monitoring, Ch. 15](https://www.amazon.com/Applied-Network-Security-Monitoring-Collection/dp/0124172083) — if available; chapter 15 is the best practitioner treatment of the live vs. dead acquisition decision.

## Key concepts
- Forensic imaging reads every raw sector, not just what the filesystem presents.
- `dc3dd` computes the hash inline, proving the image was accurate at the moment of capture.
- Dead-box acquisition preserves non-volatile integrity; live acquisition preserves volatile state.
- Memory is the highest-volatility artifact — capture it first on a live system.
- Document tool version, acquisition time, and hash for every image you take.
- E01 format is the industry standard for disk images; raw is acceptable for lab work and small images.
- Write-blocking is mandatory before touching source media in dead-box acquisition.

## AI acceleration
A model is useful for drafting acquisition checklists, case note templates, and hashing scripts. Where AI is not a substitute: computing hashes, running acquisition tools, and making the live-vs-dead-box judgment call. Feed the model your scenario (machine type, suspected attack, investigation goals) and ask it for an acquisition decision tree — then validate each branch against the NIST guidance before you execute.
