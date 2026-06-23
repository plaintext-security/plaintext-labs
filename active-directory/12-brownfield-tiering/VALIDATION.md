# Validation — Lab 12: Tiering a Brownfield Domain

## What was built

A **deterministic simulation** of a flat (brownfield) Meridian AD domain and the staged
tiering migration that closes its primary attack path. No live Samba DC is provisioned;
the domain's logon-rights state and PATH-001 are modelled as committed JSON graphs and the
attack is a reachability check over them.

Files:
- `Dockerfile`, `docker-compose.yml`, `Makefile` — one-command environment (Debian + Python3 + ldap-utils).
- `data/baseline.json` — the FLAT brownfield state: who can log on where, tier assignment, the gotcha service account, the legitimate-work hosts each admin needs.
- `data/path-001.json` — PATH-001 (from Module 08) annotated for tiering: which hop each control closes and the precondition it removes.
- `data/waves.json` — the worked-example wave plan (pilot OU -> Protected Users -> widen), each wave's mutations + two-part proof + rollback.
- `flat-walk.py` — re-walks PATH-001 on the flat baseline and proves it reaches Domain Admin (the t=0 "before" proof).
- `wave-check.py` — **the deliverable**: applies a wave's mutations and runs the two-part gate — (a) no admin locked out, (b) the targeted PATH-001 hop is dead — exiting non-zero if either fails. Supports `--wave <id>` and `--cumulative`.

## Run it

```bash
cd plaintext-labs/active-directory/12-brownfield-tiering
make up        # build the image, start the lab container
make demo      # BEFORE: PATH-001 open on the flat domain; then dead after tiering in waves
make down
```

`make before` runs only the t=0 proof; `make check` runs the cumulative per-wave gate;
`make shell` drops you in to run `python3 wave-check.py --wave wave-1 --json` etc.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose`).
- No internet needed at run time (base image layer aside); no credentials, no external target.

## Verified

Scripts were executed directly with the system `python3` (stdlib only — no third-party deps):
- `flat-walk.py` exits 0 and shows PATH-001 OPEN end-to-end on the flat baseline.
- `wave-check.py --cumulative` exits 0: all three waves PASS (no lockout AND attack dead).
- Inversion-safety confirmed: a wave that denies `tallen` on his legitimate jump host scores
  **FAIL** on assertion (a); a no-op wave that doesn't close hop 3 scores **FAIL** on
  assertion (b). A still-working attack is never scored as pass.

Not run inside Docker here (Docker unavailable in the authoring environment), but the image
is a thin Debian + Python3 layer and the scripts are stdlib-only, so `make up && make demo`
on a clean Linux runner exercises the exact code paths verified above. **No `.ci-demo` marker
added** — per the lab-quality convention, add it only after `make up && make demo && make down`
has actually been run green on a Linux runner.

## Gap to a full Samba-DC version (what a real DC would add)

This is a simulation by deliberate choice, for the same reason Module 09 is: **Samba4 does
not enforce client-side GPO user-rights.** The controls that actually kill PATH-001 —
`SeDenyInteractiveLogonRight` / `SeDenyRemoteInteractiveLogonRight` and Protected-Users
credential-caching behaviour — are enforced by the **Windows LSA on a domain-joined client**,
which these labs do not ship. Querying Samba would tell you the GPO *exists*, not that the
logon was *blocked* or that the cached credential became *non-harvestable*. So a live-DC
variant cannot answer the lab's core question (did the deny take effect?) any more reliably
than this graph does — but it would add real fidelity in three ways:

1. **Real GPO authoring.** Write the Deny-logon user-rights GPO and scope it to a pilot OU
   via `samba-tool gpo` (or RSAT/GPMC against the Samba DC), instead of the JSON `deny_logon`
   mutation — so the learner practices the actual link/filter mechanics and blast-radius scoping.
2. **A Windows client to enforce it.** Join a Windows VM to the Samba domain so the deny is
   actually applied at logon (attempt an interactive logon as `tallen` and watch it be refused
   on the pilot host but succeed on the jump host).
3. **The real attack re-walk.** Run `secretsdump.py` / an LSASS dump against the client before
   and after the wave to show the DA credential present then absent — the live form of
   `wave-check.py`'s assertion (b). This needs a Windows endpoint, hence VM/cloud territory,
   which is why the reference AD labs simulate rather than ship one.

The **judgement** the lab teaches — wave ordering by blast radius, spotting the service
account that silently logs on interactively (`svc-backup`), and scoring a *failed* attack as
pass — is identical in both forms and is the part `wave-check.py` encodes.
