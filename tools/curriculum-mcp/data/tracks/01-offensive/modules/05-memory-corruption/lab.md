# Lab 05 — Overflow a Buffer and Take Control

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/05-memory-corruption
make up
```

The container ships `gcc`, `gdb`, and `python3`. The vulnerable C program
(`src/vuln.c`) is compiled inside the container with mitigations disabled
so the mechanism is visible.

## Scenario

Meridian Financial's intranet auth stub (`meridian-login`) was compiled by a
junior dev without hardening flags. You've got the binary. Demonstrate stack
smashing: find the offset that controls the saved instruction pointer, then
redirect execution to a function that was never supposed to be reachable.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Read `src/vuln.c`. Identify the vulnerable line and draw the stack frame:
   - Where is `buf[64]` relative to the saved return address?
   - What local variable is between `buf` and the saved RBP?
   - From the frame, predict the offset (in bytes) that reaches the saved instruction
     pointer. (`make demo` runs the validated pipeline end-to-end — use it to check your
     prediction *after* you've worked it out, not before.)

2. [ ] Confirm the overwrite yourself in gdb: build the binary, feed it a long cyclic
   input, and read the instruction pointer after the crash. (`make shell` gives you `gcc`,
   `gdb`, and `python3`; a cyclic/De Bruijn pattern lets you read the offset straight off
   the clobbered register — which register holds it on x86-64?)

3. [ ] Trace `exploit.py` and explain how it works without you in the loop:
   - How does `get_win_addr()` find the target address?
   - How does `find_offset()` confirm the right offset without gdb?
   - What byte sequence does packing the `win()` address produce, and why little-endian?

4. [ ] Craft your own payload that redirects execution to `win()` and fire it at the
   binary. Confirm you reached it (the function sets a distinctive exit code). When the
   pointer is junk instead, the exit code goes negative — why, and what does a register
   full of your filler byte tell you?

5. [ ] In `src/vuln.c`, add `-fstack-protector` to the compile command in the
   comment, then compile manually and re-run the overflow payload. What changes?

## Success criteria — you're done when

- [ ] You can draw the stack frame for `vuln()` and explain why the offset to the saved
  return address is what it is.
- [ ] You redirected execution to `win()` (exit code 42) with your own crafted payload.
- [ ] You can explain what mitigations (canary, ASLR, NX) each individually prevent — and why "NX alone" doesn't stop ret2win.
- [ ] You can state why memory-safe languages (Rust, Go) eliminate this class entirely.

## Deliverables

`overflow.md`: the vulnerable line, the stack diagram with offsets, the exploit
payload (hex), and a three-line argument for which mitigation matters most.
(Don't commit compiled binaries.)

## Automate & own it

**Required.** Write or extend `exploit.py` to:
- Accept a target binary path as an argument
- Automatically find the offset and any `win()`-style function
- Output a crafted payload to stdout (for piping)

AI drafts the script; you step through each function in gdb to verify the
offsets before committing. Commit `exploit.py` and `overflow.md`.

## AI acceleration

Ask a model to annotate the disassembly of `vuln()` (paste the `objdump -d`
output) and explain each instruction. Then verify against gdb — the model
accelerates reading assembly; the debugger is ground truth.

## Connects forward

This is the primitive under every "RCE via memory corruption" CVE. Track 04
(malware) references shellcode injection; Track 06 (Active Directory) covers
ROP chains used in privilege escalation from kernel exploits.

## Marketable proof

> "I can demonstrate a stack buffer overflow — from crash to controlled
> instruction pointer — and explain the mitigation chain (canary → ASLR → NX)
> and why each one alone is insufficient."

## Stretch

- Recompile with `-fstack-protector` and observe the canary inserted between
  the buffer and saved RBP. What error does GCC emit when you overflow?
- Recompile with `-pie` (ASLR-enabled) and try to run the same exploit. Why
  does it fail? What would you need to make it work again?
