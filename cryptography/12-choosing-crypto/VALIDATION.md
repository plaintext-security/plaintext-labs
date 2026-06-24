# Validation — Module 12 (Choosing Your Crypto)

A light, writing-centric env: the only runnable piece is the dependency-free
`adr-lint.py`. The linter itself was validated against the bundled samples on
the host (Python 3); the Docker wrapping follows repo conventions but the
`make` flow has not been executed on a clean runner.

## One-line validation

```bash
make up && make demo && make down
```

`make demo` runs the linter over both bundled samples:
- `data/sample-adr-good.md` — passes (exit 0).
- `data/sample-adr-bad.md` — fails (exit 1): it trips all three checks at once
  (no standard cited, empty Consequences, missing "What would change this"),
  proving the gate fires on bad input.

## Host prerequisite

Just Python 3 (3.12-slim in the image; the linter uses stdlib only — no pip
install). Confirmed working on host Python 3:

```bash
python3 adr-lint.py data/sample-adr-good.md   # PASS, exit 0
python3 adr-lint.py data/sample-adr-bad.md    # FAIL, exit 1
```

## Files

- `adr-lint.py` — the gate (five required sections, a standard-citation regex,
  empty-section checks for Consequences / "What would change this").
- `data/adr-template.md` — the five-field ADR skeleton learners copy.
- `data/sample-adr-good.md` — a complete worked AEAD ADR (passes).
- `data/sample-adr-bad.md` — a deliberately broken KDF ADR (fails).

## Do NOT add `.ci-demo`

Not added by design, per the task. `make demo` intentionally includes a
non-zero exit from the broken-sample lint; CI marking is a separate decision for
the maintainer once the full `make up && make demo && make down` flow is green
on a Linux runner.
