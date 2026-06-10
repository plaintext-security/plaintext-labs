# AI-Augmented Security Operations capstone — grading rubric

Self/peer/reviewer rubric for the Track 12 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **The copilot** | Bare LLM call, no grounding/tools | MCP server exposing one real tool, grounded in a RAG corpus of your notes | Genuinely useful for a SOC task; retrieval relevant and tools scoped |
| **The attack** | Theoretical, not demonstrated | A working prompt-injection or data-exfil exploit shown against your own system | Mapped to OWASP LLM Top 10 / MITRE ATLAS; shows real impact |
| **The fix** | Generic advice, not applied | A concrete hardening that defeats the demonstrated attack | Re-tested: same attack now fails; defence-in-depth (input + tool-scoping + output) |
| **Tool & data scoping** | Tools/access unbounded | Tools and retrieval scoped to least privilege | Untrusted content can't reach privileged tools; trust boundary explicit |
| **Write-up** | Disconnected pieces | Build → attack → fix told as one coherent story | Honest about residual risk and what the model can still be tricked into |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Test prompt-injection and jailbreak techniques only against models and applications you own or are authorised to assess.
