# Module 06 — Memory Forensics

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *RAM is the one place an attacker cannot clean up and leave — everything running exists in memory.*

## Why this matters
Advanced attackers go to great lengths to avoid touching disk: fileless malware runs entirely in memory, injected shellcode lives inside legitimate processes, encryption keys are decrypted at runtime and never written to a file. A traditional disk investigation sees none of this. Memory forensics is the technique that reveals what is actually running — processes, their injected payloads, their network connections, the decryption keys in use — from a single memory capture. For a sophisticated intrusion, memory is often the *only* place the full picture exists.

## Objective
Use Volatility3 to analyze a memory image: enumerate running processes, identify network connections, extract process command lines, find evidence of process injection, and explain what each finding tells you about attacker behavior.

## The core idea
A memory image is a dump of physical RAM at a moment in time — every bit of every process, the kernel, device drivers, and the OS's own data structures, all in one flat binary file. Volatility3 navigates this raw binary by applying *symbol tables* (debug symbols for the specific kernel version) that tell it exactly where, in this particular OS build, the process list, network table, and other structures live. This is why Volatility3 requires a profile that matches the captured system — the data structures for Windows 10 build 22H2 are in different locations than Windows Server 2019, and the wrong profile produces garbage. Once the profile is right, Volatility3 can walk the kernel's linked list of processes (`pslist`), read each process's virtual address space, and reconstruct almost everything the OS knows.

**The most important Volatility3 plugin for IR is `pslist` — but the most important one for detecting malware is `pstree` paired with `cmdline`.** The process tree reveals the parent-child relationships that malware exploits: a web server that spawned `cmd.exe`, or a `Word.exe` that spawned `powershell.exe -enc`. These parent-child anomalies are the most reliable behavioral signal for initial access and execution. `cmdline` reveals the exact command line every process was launched with — including encoded PowerShell payloads, credential-harvesting flags, and lateral movement commands that were never written to disk.

**Process injection** is the technique that makes memory forensics essential. An attacker injects shellcode or a DLL into a legitimate process — `svchost.exe`, `explorer.exe`, `notepad.exe` — so that their malicious activity runs under a trusted process name and evades process-based controls. Volatility3's `malfind` plugin detects injection by looking for memory regions inside a process's virtual address space that are executable, contain no mapped file on disk, and exhibit tell-tale byte patterns (PE headers, shellcode stubs). A `malfind` hit is a lead, not a conviction — some legitimate software (JIT compilers, DRM) allocates executable anonymous memory — but an executable anonymous region inside `notepad.exe` warrants investigation.

**Network connections in memory** are often more complete than the OS's own `netstat`, because the memory image captures the kernel's socket and connection tables directly, including connections that may have been opened and closed recently. `netstat` (in Volatility3) shows established connections, listening ports, and recently-closed connections — all tied to the owning process. A connection from `svchost.exe` to a non-Microsoft external IP is immediately suspicious. A connection from `notepad.exe` to port 443 is definitive evidence of injection, because `notepad.exe` has no legitimate reason to make network calls.

## Learn (~4 hrs)

**Volatility3 fundamentals (~2 hrs)**
- [Volatility3 documentation — GitHub](https://github.com/volatilityfoundation/volatility3) — the README covers installation, profile selection, and the most used plugin list. Read the Usage section and the plugin reference.
- [Volatility Foundation Cheat Sheet (PDF)](https://downloads.volatilityfoundation.org/releases/2.4/CheatSheet_v2.4.pdf) — the original cheat sheet for core plugins; some plugin names differ in v3 but the concepts are identical. A useful quick reference.
- [Memory Forensics with Volatility3 — 13Cubed YouTube playlist](https://www.youtube.com/watch?v=Uk3DEgY5Ue8) — a practitioner walkthrough of pslist, pstree, cmdline, netscan, and malfind; approximately 30 minutes total. Watch before the lab.

**Memory acquisition and images (~1 hr)**
- [Acquiring Memory for Incident Response — SANS poster](https://www.sans.org/posters/memory-forensics-cheat-sheet/) — concise reference covering Windows (WinPmem, DumpIt) and Linux (avml, LiME) acquisition tools.
- [MemLabs — GitHub](https://github.com/stuxnet999/MemLabs) — a set of beginner-friendly CTF memory forensics challenges with publicly available images; Lab01 is a good first target after this module.

**Process injection detection (~1 hr)**
- [MITRE ATT&CK T1055 — Process Injection](https://attack.mitre.org/techniques/T1055/) — the definitive breakdown of injection sub-techniques; maps what `malfind` is detecting to the ATT&CK taxonomy.

## Key concepts
- A memory image is a snapshot of physical RAM; Volatility3 uses kernel symbol tables to parse it.
- Profile selection must match the exact OS build — wrong profile, garbage output.
- `pslist`/`pstree` reveal process hierarchy; parent-child anomalies are the primary execution signal.
- `cmdline` reveals the exact launch command for every process, including encoded payloads.
- `malfind` finds injected code by looking for executable, file-less memory regions in process space.
- `netstat`/`netscan` shows socket and connection tables from the kernel, including recently-closed.
- Process injection (T1055) is the primary reason memory forensics surfaces what disk analysis misses.
- A `malfind` hit is a lead; triage by correlating with `pslist` parent and `netscan` connections.

## AI acceleration
AI is useful for explaining Volatility3 output — feed it a `pslist` dump and ask it to flag anomalous parent-child relationships. For `malfind` hits, feed the disassembled bytes and ask whether they look like shellcode or a JIT stub. Where AI is not reliable: it cannot run Volatility3 against your image, and it will hallucinate specific offsets and process details. Use it to interpret output you've already captured; every finding must trace back to the actual plugin output.
