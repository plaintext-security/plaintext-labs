# Lab 06 — Memory Forensics

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/06-memory-forensics
make up        # build the Volatility3 container
make demo      # analyze pre-processed Volatility3 output (pslist, netscan, cmdline, malfind)
make shell     # drop in to work interactively
make down      # stop when done
```

**About the memory image:** Full Windows memory images are gigabytes in size — too large to commit.
This lab ships `data/memory-sample.json` — pre-processed Volatility3 output (pslist, netscan,
cmdline, malfind) from a synthetic Meridian incident scenario. The demo analyzes this output directly.

**To run Volatility3 against a real memory image yourself:**
1. Acquire a training image from [MemLabs](https://github.com/stuxnet999/MemLabs) (free, ~1GB, publicly licensed for learning).
2. Place it in `data/memory.img` (not committed — add to `.gitignore`).
3. Run `make analyze IMAGE=data/memory.img` to run Volatility3 plugins against it.

> Only analyze memory images you have explicit authorization to examine.

## Scenario
The Meridian IR team captured a memory image from `MERIDIAN-FIN-WS01` before shutdown (collected using `avml` per Module 02 procedures). The image has been processed through Volatility3; the plugin output is in `data/memory-sample.json`. Your task is to analyze the process list, network connections, command lines, and injection findings to answer: **What malware ran? How did it persist in memory? What network connections did it make?**

> Only analyze memory images you are authorised to examine. A memory image contains everything running on the system at capture time, including sensitive data.

## Do

1. [ ] **Analyze the process list (`pslist` output).**
   Open `data/memory-sample.json` and examine the `pslist` section.
   - Which processes are running? Does any process have an unexpected parent (e.g., `notepad.exe` parented by `cmd.exe`)?
   - Are there any processes with suspicious names that mimic legitimate Windows processes (e.g., `svchost.exe` outside `C:\Windows\System32\`, or `svch0st.exe`)?
   - Note the PIDs of suspicious processes for cross-referencing.

2. [ ] **Examine command lines (`cmdline` output).**
   In the `cmdline` section:
   - Find any process with an encoded PowerShell argument (`-enc`, `-EncodedCommand`).
   - Decode the encoded argument. (PowerShell `-enc` takes base64 of UTF-16LE text — decode it
     the right way or you'll get mojibake; which decoder and what about the wide-char encoding?)
   - What does the decoded command do? Is it consistent with the incident scenario?

3. [ ] **Examine network connections (`netscan` output).**
   In the `netscan` section:
   - Which processes have established outbound connections?
   - Are any connections made by processes that should not be making network calls (e.g., `notepad.exe`, a suspended process)?
   - Note destination IPs and ports. Does any destination match the C2 address from the earlier
     scenario modules? Record the IP and port you find.

4. [ ] **Triage injection findings (`malfind` output).**
   In the `malfind` section:
   - Which processes have executable, file-less memory regions?
   - What are the first bytes of the suspicious region? Do they look like a PE header (`MZ`, `4D5A`) or shellcode?
   - Cross-reference: does the injected process also appear in `netscan` with an outbound connection? This combination (injection + outbound connection) is the strongest behavioral indicator.

5. [ ] **Build an attacker timeline from memory evidence.**
   Write `memory-findings.md` with:
   - Process tree showing the suspicious parent-child chain
   - Decoded PowerShell payload and what it does
   - Network connections attributed to the malicious process
   - `malfind` hit details (process, PID, memory region, first bytes)
   - Short paragraph: what would you look for next on disk, and what artifacts would confirm or deny what the memory evidence suggests?

## Success criteria — you're done when
- [ ] At least one anomalous parent-child process relationship is identified and documented.
- [ ] The encoded PowerShell payload is decoded and its purpose explained.
- [ ] Network connections from suspicious processes are documented with destination IPs/ports.
- [ ] At least one `malfind` hit is documented and triaged.
- [ ] `memory-findings.md` includes a timeline narrative and a "next steps" paragraph.

## Deliverables
Commit `memory-findings.md` to your fork. Do not commit memory image files — they are too large and may contain sensitive data.

## Automate & own it
**Required.** Write a Python script `memory-triage.py` that:
1. Reads `data/memory-sample.json`.
2. For the `pslist` output, flags any process whose parent PID does not match a known-good parent (e.g., `cmd.exe` parented by anything other than `explorer.exe` or `services.exe`).
3. For the `netscan` output, flags any connection from a process not in a whitelist of network-capable processes.
4. Produces a Markdown triage report.

Have a model draft the logic; **read every line** and validate the parent-PID logic against the sample data before committing. This is the automation move for memory triage at scale.

## AI acceleration
Feed the `pslist` output to a model and ask it to identify anomalous parent-child relationships. Feed the first 16 bytes of a `malfind` hit and ask whether it looks like a PE header, shellcode, or a JIT stub. Cross-check every finding the model names against the actual JSON data — models will confabulate specific PIDs and process names.

## Connects forward
Memory evidence feeds the super-timeline in Module 07 (timestamps from memory corroborate disk and log events). The injected process and its network connection connect to Module 09 (network forensics — you'd look for the C2 traffic in PCAP) and Module 12 (the payload extracted from the `malfind` region goes to malware analysis).

## Marketable proof
> "I analyze memory images with Volatility3 — surfacing injected code, encoded payloads, and covert network connections that never touched disk."

## Stretch
- Download MemLabs Lab 01 (free, ~1GB) and run the full Volatility3 pipeline against it: `pslist`, `pstree`, `cmdline`, `netscan`, `malfind`. Document your findings in a structured report.
- Research the difference between `pslist` (walks the kernel's PProcess doubly-linked list) and `psscan` (scans the full memory image for EPROCESS pool tags). Why might a rootkit appear in `psscan` but not `pslist`?
