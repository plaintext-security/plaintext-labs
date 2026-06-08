# plaintext-labs

> The runnable companion to the [Plaintext](https://github.com/plaintext-security/plaintext)
> security curriculum. Dockerfiles, lab environments, seed data, and capstone starters —
> everything you *run*, so the curriculum stays everything you *read*.

Plaintext is split across two repos:

| Repo | Holds | You… |
|------|-------|------|
| [`plaintext`](https://github.com/plaintext-security/plaintext) | the curriculum prose — module concepts, the *Learn* path, lab instructions | **read** it (published at the site) |
| `plaintext-labs` (this repo) | the runnable scaffolding — `docker-compose`, Dockerfiles, seed data, harnesses, capstone starters | **clone & build** it |

A lab's *instructions* live in `plaintext`; its *environment* lives here. Each lab tells you which
directory to `make up`.

## Layout

```
plaintext-labs/
├── <track>/                         # foundations, offensive, defensive, forensics, …
│   ├── <NN-module-name>/            # one self-contained lab environment per module
│   │   ├── docker-compose.yml           # the lab, one command to stand up
│   │   ├── Makefile                     # up / down / reset / demo [/ shell]
│   │   ├── data/                        # small, curated seed data (committed)
│   │   └── …                            # Dockerfile, helper scripts, examples
│   └── capstone/                    # the track's portfolio project starter (skeleton + CI, no solutions)
└── …
```

## Quickstart

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/08-detection-as-code
make up      # build + start the lab environment
make demo    # see the worked example (where a lab provides one)
make down    # stop it
```

Then follow that module's `lab.md` in the [curriculum](https://github.com/plaintext-security/plaintext).

## Conventions (every lab dir follows these)

- **One command up.** A `docker-compose.yml` + a `Makefile` exposing `up` / `down` / `reset` /
  `demo` (and `shell` where useful). `make up` and the lab is live — no multi-step setup.
- **Small seed data is committed; heavy artifacts are not.** Curated samples that make the lab
  real (a slice of logs, a few events) live in `data/`. Packet captures, disk/memory images,
  malware samples, and verbose logs are *downloaded or generated* by the lab — never committed
  (see `.gitignore`).
- **We give the starting line, not the solution.** Capstone starters ship the environment, the
  brief, failing tests / CI, and TODO skeletons. The student builds the rest in their own repo —
  that's the portfolio proof.
- **Pinned and reproducible.** Image tags and tool versions are pinned so a lab built today builds
  the same next year.

## Capstones

Each track's `capstone/` is a starter the learner builds upon across the whole track — a real,
continuous project (the kind of thing you put on a résumé). It is *scaffolding*, not an answer key.

## License

Dual-licensed, the standard split for an open-education project:

- **Lab content & seed data** — [CC BY 4.0](LICENSE)
- **Tooling & code** (Dockerfiles, scripts, Makefiles, harnesses) — [MIT](LICENSE-CODE)

Use it, share it, build on it.
