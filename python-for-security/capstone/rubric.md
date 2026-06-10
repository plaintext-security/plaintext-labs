# Python for Security capstone — grading rubric

Self/peer/reviewer rubric for the Track 09 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Usefulness** | A toy re-implementing a one-liner | Solves a real security task you'd actually reach for | Fills a real gap; handles a workflow start to finish |
| **Code quality** | Monolithic; no error handling | Structured, handles malformed input, passes `ruff`, has `--help` | Idiomatic, typed, packaged installable; clean separation of concerns |
| **Tests** | None, or happy-path only | `pytest` covering core logic *and* edge/malformed input | Meaningful coverage incl. failure modes; tests run in CI |
| **Robustness** | Crashes on bad input/API errors | Fails gracefully; rate-limits/retries on API calls | Secrets handled safely (env, not hardcoded); validates input |
| **Ownership of AI code** | Pasted AI output unread | Write-up names what AI generated and what you changed and why | Documents a caught bug/risk in the generated code that you fixed |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] No live target needed; if the tool talks to an API, use your own keys (env vars, never committed).
