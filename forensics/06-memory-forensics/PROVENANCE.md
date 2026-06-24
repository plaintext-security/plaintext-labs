# Provenance — Lab 06 Memory Forensics data

## Primary real dataset: MemLabs Lab 1 "Beginner's Luck"

- **Dataset:** MemLabs — a set of real Windows memory dumps designed as CTF challenges, analyzable
  end-to-end with Volatility (2 and 3). This lab uses **Lab 1 "Beginner's Luck"** as the primary
  real memory image.
- **Author / source:** stuxnet999, https://github.com/stuxnet999/MemLabs
  Lab 1 folder: https://github.com/stuxnet999/MemLabs/tree/master/MemLabs%20Lab%20Setup
  (the per-lab README in the repo links the Google-Drive-hosted image).
- **License / status:** public CTF/educational challenge set; freely usable for learning. The memory
  image (~1GB) is **Google-Drive-hosted** via the repo's README — there is **no stable direct
  download URL**, so we do not record or guess one. The learner follows the MemLabs repo README to
  fetch it.
- **How it is used here:** the real MemLabs Lab 1 dump is the **primary artifact** — placed at
  `data/memory.img` (gitignored) and run with `make analyze IMAGE=data/memory.img` through the full
  Volatility3 pipeline (`pslist`, `pstree`, `cmdline`, `netscan`, `malfind`). It replaces the prior
  synthetic seed as the real artifact. The pre-processed `data/memory-sample.json` is retained as the
  offline demo seed.

### How to fetch (manual — no direct URL)

`make fetch-data` prints these steps:

1. Open https://github.com/stuxnet999/MemLabs
2. Go to Lab 1 ("MemLabs Lab Setup" folder) and follow its README download link to the
   Google-Drive-hosted image.
3. Unzip and place the dump at `data/memory.img` (gitignored, not committed).
4. Run `make analyze IMAGE=data/memory.img`.

### SHA-256 (fill after fetch)

Run `sha256sum data/memory.img` after fetching and record here to pin the artifact:

```
<fill after fetch>  memory.img  (MemLabs Lab 1 "Beginner's Luck")
```

> Fetch and SHA-256 validation are **deferred to runner-validation** — the Drive-hosted image has
> not been downloaded in authoring.

## Demo seed (retained)

- `data/memory-sample.json` — pre-processed Volatility3 output (pslist / cmdline / netscan /
  malfind) modelled on the **Lunar Spider** intrusion technique chain (see `../ANCHOR.md`) with
  neutral naming (host `BEACHHEAD-WS01`). Offline fallback so `make demo` runs before the real
  image is fetched. It replaces the prior synthetic seed.
