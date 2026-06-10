# Module 05 — Memory Corruption Primer

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *why a program crashes is often why it gets exploited.*

## Why this matters
Memory-corruption bugs — buffer overflows and their relatives — are the root of a huge share
of the most severe CVEs, and out-of-bounds writes sit at the very top of the CWE "most
dangerous weaknesses" list. You don't need to become an exploit developer, but you do need to
understand *why* writing past a buffer hands an attacker control, so a vulnerability class
like "stack overflow" stops being a magic phrase.

## Objective
Explain how a stack-based buffer overflow hijacks execution, and demonstrate one against a
simple vulnerable program in your lab.

## The core idea
Most vulnerability classes so far have been about *data* crossing a boundary (injection). Memory
corruption is different: it's about the program's own **control flow** being hijacked by writing
where you shouldn't. The canonical case: a function keeps its return address on the stack right next
to a local buffer; overflow the buffer and you overwrite that saved return address; when the function
returns, the CPU jumps wherever you wrote. That's the entire magic trick — "smash the stack"
demystified into "overwrite the saved instruction pointer and the processor executes your address."
Out-of-bounds writes sit at #1 on the CWE most-dangerous list for exactly this reason.

You don't need to become an exploit developer, but you need this model so "buffer overflow" stops
being a magic phrase and becomes a mechanism you can reason about — and so you understand *why*
memory-safe languages (Rust, Go) exist and what the mitigations are defending. Those mitigations are
an arms race: **ASLR** randomises addresses so you don't know where to jump, **stack canaries** plant
a guard value that detects the overwrite, **NX** marks the stack non-executable. Each raised the bar,
which is why modern exploitation is largely about *bypassing* them — and why real exploits chain
several tricks rather than just overflowing a buffer.

The practitioner payoff: this is the bedrock under "RCE" in the scariest CVEs. When you read "remote
code execution via a heap overflow," this is what's happening underneath — and now it's a mechanism,
not a headline. A model is a patient tutor for the assembly and the stack diagram (ask it to annotate
a disassembly or explain a canary), but generated exploit code for memory bugs is fiddly and
version-specific: you *will* debug it by hand, and that debugging is exactly where the understanding
forms.

## Learn (~4 hrs)

**Concept, then hands-on**
- [Intro to Binary Exploitation — Buffer Overflows #0: Intro / Basics / Setup (video)](https://www.youtube.com/watch?v=wa3sMSdLyHw) — a beginner-friendly start to how stack overflows work.
- [pwn.college (Arizona State, free)](https://pwn.college/) — work the **Memory Errors / Program Security** modules; the best free hands-on path into binary exploitation.

**Why it matters at scale**
- [MITRE CWE-787 — Out-of-bounds Write](https://cwe.mitre.org/data/definitions/787.html) — consistently the #1 most dangerous software weakness; the class you're learning.

## Key concepts
- The stack, the saved return address, and control flow
- What "overflow the buffer" actually overwrites
- Why this hands the attacker the instruction pointer
- Modern mitigations (ASLR, stack canaries, NX) — at a high level
- Memory-corruption classes (overflow, use-after-free, out-of-bounds write)

## AI acceleration
A model is a patient tutor for the concepts and the assembly — ask it to annotate a
disassembly or explain a stack canary. But generated exploit code for memory bugs is fiddly
and version-specific; expect to debug it yourself, which is exactly where the understanding
forms.
