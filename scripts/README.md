# Lab tooling (`scripts/`)

Plaintext is an **honor-system** curriculum. There is **no grading, no receipts, and no credentials** —
learning is the point, and that's on all of us. A lab's "Success criteria" are things you verify *for
yourself*; the artifact you commit to your own portfolio repo is the proof, to you and to anyone who reads
it. (See the curriculum's `start-here` and `showcase` pages for the portfolio-as-proof model.)

These scripts are **maintainer/author tooling**, not learner grading:

- **`check_consistency.py`** — asserts the curriculum prose (`plaintext/tracks/`) and the labs here stay
  in lockstep (a module that exists in one repo exists in the other, nav is complete, etc.). Run in CI.
- **`local-lab-check.sh`** — runs lab `make demo`s on your machine to see how they fare before you push
  (a developer convenience, not a check a learner needs). `--all` sweeps every lab with a `make demo`.
- **`promote_ci_demo.sh`** — adds a `.ci-demo` marker to labs that passed the survey and opens a PR, so a
  green result becomes a standing regression gate. Called by the **Labs Survey** workflow, or run locally:
  `scripts/local-lab-check.sh --all | awk '$2=="PASS"{print $1}' > greens.txt && scripts/promote_ci_demo.sh greens.txt`.
- **`tests/`** — unit tests for the tooling above.

## Validating labs at scale: the survey

You don't hand-run ~175 labs. Two CI workflows split the job:

- **`labs-ci.yml`** (the gate) — runs only `.ci-demo` labs; a failure fails the build. Keeps *validated*
  labs from rotting.
- **`labs-survey.yml`** (the scout) — runs **every** lab with a `make demo` (minus `.ci-skip`),
  `continue-on-error`, and reports a PASS/FAIL scorecard; with `promote: true` it opens a PR adding
  `.ci-demo` to the green ones. Trigger it from the Actions tab (workflow_dispatch) or let the weekly run
  produce the scorecard. This is how the un-validated backlog gets a verdict without anyone running them by
  hand.

To take a lab **out** of the survey (genuinely can't run on a clean Ubuntu+Docker runner — real cloud
creds, a real VM, paid SaaS), drop a **`.ci-skip`** file in its dir whose contents say why. Note: the cloud
track mostly runs on **LocalStack**, so it does *not* need skipping — let the survey prove it.

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
