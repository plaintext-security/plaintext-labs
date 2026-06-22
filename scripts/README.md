# Lab tooling (`scripts/`)

Plaintext is an **honor-system** curriculum. There is **no grading, no receipts, and no credentials** —
learning is the point, and that's on all of us. A lab's "Success criteria" are things you verify *for
yourself*; the artifact you commit to your own portfolio repo is the proof, to you and to anyone who reads
it. (See the curriculum's `start-here` and `showcase` pages for the portfolio-as-proof model.)

These scripts are **maintainer/author tooling**, not learner grading:

- **`check_consistency.py`** — asserts the curriculum prose (`plaintext/tracks/`) and the labs here stay
  in lockstep (a module that exists in one repo exists in the other, nav is complete, etc.). Run in CI.
- **`local-lab-check.sh`** — runs lab `make demo`s on your machine to see how they fare before you push
  (a developer convenience, not a check a learner needs).
- **`tests/`** — unit tests for the tooling above.

## The lab contract (what every lab still provides)

Each lab ships a `Makefile` with the standard targets — **`up` · `down` · `reset` · `demo`** (and
`shell`/`check` where useful). A lab is *done* when `make up && make demo && make down` is green on a
Linux runner; add a `.ci-demo` marker only then, and only for labs whose demo is expected to pass in CI
(not learner-exercise labs whose demo fails until the learner finishes, and not VM/cloud labs). This is
**lab quality assurance**, not learner grading.

## How a learner knows they're done

The lab's `lab.md` lists measurable **Success criteria** ("you're done when…") and a **Deliverable** (the
portfolio artifact). You check the criteria yourself and commit the deliverable. No tool gates it; no
credential is issued. That's the honor system — and the only credential is the work in your repo.
