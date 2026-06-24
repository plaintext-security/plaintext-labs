# Lab 11 — PQC Migration: Move a TLS Service to Hybrid X25519+ML-KEM Without Breaking Interop

*Type 12 · Migration / Brownfield. [← Back to the module concept](README.md)*

**Type 12 · Migration / Brownfield.** You take a running TLS service on **classic ECDHE/RSA** — the
shape every web service ships today — and migrate its key exchange to a **hybrid post-quantum** suite
(`X25519MLKEM768`) *incrementally*, the strangler-fig way: inventory what crypto it actually negotiates,
**add** the hybrid group *alongside* the classical ones (never swap it out), and prove at every step that
**nothing broke** — a modern client now negotiates the hybrid (quantum-safe) path *while a legacy client
still connects classically*. The deliverable is the *crypto inventory + the migrated config + before/after
handshake captures proving interop is preserved* — not a writeup. No grader; you verify your own work
against the observable success criteria below. (Honor system: the committed inventory, the migrated config,
and the before/after captures are the proof.)

## Setup

> **Lab env to be built & validated** — this is the Cryptography track's first Type 12 and has **no
> existing `plaintext-labs` directory wired yet**. The shape below is the spec (see the **Lab-env spec** at
> the end of this file); `make up`/`make demo` have **not** yet been run on a clean runner — building and
> validating that env is the next step before this module counts as done. Until then, every command below
> is real and runs on a laptop with Docker (or a local **OpenSSL 3.5+** build) installed — OpenSSL 3.5
> ships ML-KEM natively, so the lab needs **no third-party provider**.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/11-pqc-migration
make up          # a TLS service on classic ECDHE/RSA, plus a "modern" and a "legacy" client container
make inventory   # capture & print what the service negotiates today (the baseline crypto inventory)
make migrate     # add the hybrid X25519MLKEM768 group to the server config, keep classical fallback, reload
make verify      # before/after handshake capture: modern client → hybrid; legacy client → classical; both 200
make rollback    # remove the hybrid group, restore the classical-only config (the migration's rollback)
make shell       # drop into a client container to run openssl s_client / curl by hand
make down
```

`make up` stands up an **nginx (or OpenSSL `s_server`) TLS endpoint configured exactly as a brownfield
service is today**: TLS 1.2/1.3, ECDHE key exchange, an RSA server certificate — *no post-quantum
anything*. Two client containers connect to it: a **modern** client (OpenSSL 3.5+, capable of offering
`X25519MLKEM768`) and a **legacy** client (an older OpenSSL that knows only classical groups). The whole
lab is the gap between "the service offers only classical key exchange" and "the service offers hybrid to
those who can use it, and classical to those who can't" — added without an outage.

> **Authorization note:** Only test systems you own or have explicit written permission to test.
> Everything here runs locally in Docker (or against your own `localhost` OpenSSL server) — no external
> targets, no authorization needed. The handshake captures below are aimed *at your own lab service*. The
> moment you point `testssl.sh` / `s_client` at a real host: only scan and migrate crypto for
> infrastructure you own or are authorized to manage, and never disable a classical fallback in production
> before you have proven every client population can negotiate the new path.

## Scenario

A service has terminated TLS the same way for years: TLS 1.3 (and 1.2), ECDHE for key exchange, an RSA
certificate. It is fine against today's attackers — and quietly exposed to **harvest-now-decrypt-later**,
because an adversary who records its traffic now can decrypt every session once a quantum computer can
break the ECDHE key exchange. NIST finalized ML-KEM (FIPS 203) in August 2024, Chrome and Cloudflare are
already negotiating hybrid `X25519MLKEM768` on real connections, and you've been told to migrate this
service's key exchange to the hybrid suite. The one rule is **no broken interop**: the service has clients
you do not control — old mobile apps, embedded devices, a partner's integration — that understand only
classical groups, and they cannot stop connecting on the day you migrate.

So you do **not** flip the server to demand ML-KEM (that refuses every legacy client — a self-inflicted
outage dressed up as a security upgrade). You migrate the strangler-fig way: read the real handshake to
inventory what's negotiated today, **add** the hybrid group *alongside* the classical ones so TLS
negotiation routes each client to the best path it supports, and **prove with before/after handshake
captures** that a modern client now gets the hybrid (quantum-safe) exchange *while a legacy client still
completes its classical handshake unchanged*. The config is not the proof — the capture is.

The rhythm: **inventory (read the real handshake) → pick the hybrid suite → add it, keep the fallback →
capture before/after (modern=hybrid, legacy=classical, both succeed) → keep the rollback.**

## Do

Migrate the service's key exchange to hybrid X25519+ML-KEM, adding it beside the classical path and proving
interop is preserved — then keep a rollback.

**Inventory the brownfield crypto (read the handshake, not the config)**
1. [ ] `make up`, then **inventory what the service actually negotiates today** — do not trust the config
   file. From the modern client, complete a handshake and read the negotiated key-exchange group and cipher
   (hint: `openssl s_client -connect <host>:443 -tls1_3` and look at the `Negotiated TLS1.3 group` /
   `Server Temp Key` line; or run `testssl.sh` and read its key-exchange section). Record per endpoint:
   **TLS version, negotiated group (e.g. `X25519`), cipher, cert key type (RSA)** — and classify the
   key exchange as **quantum-exposed** (it is). This table is your *crypto inventory* and the BEFORE half
   of your proof.
2. [ ] **Confirm the legacy client's baseline too.** From the legacy client, complete the same handshake
   and record its negotiated classical group. You will re-run this exact test *after* migrating to prove
   the legacy path is untouched — capture it now.
3. [ ] **Name the big-bang trap before you avoid it.** In your inventory notes, write what breaks if you
   "migrate" by setting the server's supported groups to *only* `X25519MLKEM768`: every client that can't
   offer ML-KEM (the legacy client, the embedded devices, the old mobile app) fails the handshake — you've
   turned a quantum *risk* into an immediate *outage*. **You will not do this**; naming it is the point.

**Migrate — add the hybrid group, keep the classical fallback**
4. [ ] **Pick the suite and add it (additively).** Edit the server config to add `X25519MLKEM768` to the
   supported key-exchange groups **at the front of the list, with `X25519` and the classical groups still
   present behind it** (hint: nginx `ssl_ecdh_curve` / OpenSSL `-groups X25519MLKEM768:X25519:...`, or the
   `Groups`/`Curves` config directive depending on the server). The intent is explicit: *offer hybrid
   first to those who can use it; fall back to classical for those who can't.* Reload the service with no
   downtime (`nginx -s reload` / restart the `s_server`).
5. [ ] **Capture the AFTER for the modern client — prove the hybrid path negotiates.** Re-run the modern
   client's handshake and assert the negotiated group is now **`X25519MLKEM768`** (the hybrid, quantum-safe
   path), not classical `X25519`. *If it silently fell back to `X25519`, the migration did NOT happen* —
   the most common cause is an OpenSSL build without ML-KEM support, or the client not offering the group.
   Debug until the modern handshake genuinely negotiates the hybrid group. Save this capture (an
   `s_client` trace or a `pcap`/keylog showing the negotiated group).
6. [ ] **Capture the AFTER for the legacy client — prove interop is preserved.** Re-run the *legacy*
   client's handshake against the now-migrated server and assert it **still completes**, still negotiating
   its classical group, with the same result as step 2 — **no broken interop**. The legacy client never
   offered ML-KEM, TLS negotiation handed it the classical fallback, and it connected exactly as before.
   This is the strangler-fig guarantee, captured.
7. [ ] **Verify both end-to-end, not just the handshake.** From each client, confirm an actual request
   succeeds through the migrated TLS (e.g. `curl https://<host>/` → 200) — modern client over the hybrid
   path, legacy client over the classical path. The service answered both; nothing went down.

**Keep the rollback**
8. [ ] **Capture and run the rollback.** Write the one-line rollback (remove `X25519MLKEM768`, restore the
   classical-only group list, reload), then **run it**: `make rollback`. Confirm the modern client falls
   back to classical `X25519` and *still connects* (the migration was always additive, so backing out is
   cheap and breaks nothing), then `make migrate` again to restore the hybrid state. A rollback you wrote
   but never ran is not a rollback.

## Success criteria — you're done when
- [ ] You have a **crypto inventory** read from the *real handshake* (not the config): per endpoint, the
      TLS version, negotiated key-exchange group, cipher, and cert key type — with the key exchange
      classified **quantum-exposed**.
- [ ] You named the **big-bang trap** in your notes (server offering *only* the hybrid group breaks every
      legacy client — a self-inflicted outage) — the failure your additive migration avoids.
- [ ] After migrating, a **before/after handshake capture** proves both halves: the **modern** client now
      negotiates **`X25519MLKEM768`** (the hybrid, quantum-safe path — *not* a silent classical fallback),
      **and** the **legacy** client still completes its **classical** handshake unchanged — **interop
      preserved**.
- [ ] Both clients complete an actual request (200) through the migrated service — **no outage** for
      either population.
- [ ] You have a **rollback** you *ran* at least once, proving the additive change reverts cleanly with no
      broken connections (the classical path was never removed).

## Deliverables
Commit to your portfolio repo:
- `crypto-inventory.md` — the per-endpoint inventory read from the live handshake (TLS version, negotiated
  group, cipher, cert key type), each row classified quantum-exposed or not, plus the named big-bang trap
  you avoided and *why* hybrid (safe if either X25519 or ML-KEM holds).
- the **migrated config** — the actual server config (nginx `.conf` / OpenSSL `s_server` invocation /
  `Groups` directive) showing `X25519MLKEM768` **added in front of** the retained classical groups, with a
  comment explaining the additive, fallback-preserving intent.
- `handshake-proof.md` — the **before/after captures** proving nothing broke: the BEFORE (modern + legacy
  both on classical `X25519`), and the AFTER (modern now on `X25519MLKEM768`; legacy *still* on classical,
  unchanged), each as the `s_client`/`testssl.sh` line or `pcap`/keylog excerpt that shows the *negotiated*
  group — the config is not proof, the capture is.
- `rollback-note.md` — the one-line rollback (remove hybrid, restore classical-only, reload) with the one
  capture proving the modern client fell back to classical and still connected after a rollback was
  actually run.

Do **not** commit: the server's TLS private key or certificate (`*.key`, `*.pem`, `*_rsa`), any TLS
keylog/`SSLKEYLOGFILE` files used to decrypt captures, raw full `pcap`s (curate the handshake excerpt
instead), or the lab's seeded service data (it lives in the lab repo, not yours).

## Automate & own it
**Required — this is the before/after handshake check turned into a reusable migration gate.** A crypto
migration you can't *re-prove* is one you don't actually trust (and PQC support changes as libraries
update — you'll want to re-run this). Build the proof into a harness, `handshake-check.sh <host>`, that a
model drafts and **you review every line of**, asserting the migration held and exiting non-zero on any
failure:
1. **Modern client negotiates hybrid:** an OpenSSL 3.5+ `s_client -groups X25519MLKEM768` to `<host>`
   completes **and** the negotiated group parsed from the output is exactly `X25519MLKEM768` — *not*
   classical `X25519`.
2. **Legacy interop preserved:** a classical-only client handshake to `<host>` **still completes** and
   negotiates a classical group (the fallback works).
3. **Both serve a request:** each client gets a 200 through the migrated TLS.

Wire it as the `make verify` gate (run automatically after `make migrate`). **Review every line and make
it fail closed:** the dangerous bug is a harness that goes green when the modern handshake **silently fell
back to classical** — so assertion (1) must *parse the negotiated group and string-match it*, never just
check "the handshake succeeded" (a successful classical handshake is exactly the failure you're guarding
against). Likewise a connection error, a timeout, or an `s_client` that couldn't run must count as a
**failure**, never a silent pass. (AI drafts; you prove the signal is honest — that it can tell "negotiated
hybrid" from "negotiated classical and called it a win" — and you own it.)

## AI acceleration
Ask a model to draft the crypto inventory from your `s_client`/`testssl.sh` output and the migrated config
diff — then refuse to trust its plan. The model's default instinct is **big-bang**: ask it to "make this
server post-quantum" and it will hand you a config that sets the supported groups to *only*
`X25519MLKEM768`, breaking every legacy client, because demanding the new algorithm is the simplest thing
to express and it carries none of the fear of an interop outage. Make it produce the **additive** change
(hybrid in front, classical retained) and explain *why* the fallback stays. The judgment it cannot do for
you is **verifying the capture**: asked to "confirm the migration worked," a model reads your config back
and pronounces it done — missing that the handshake silently negotiated classical `X25519` because your
build lacked ML-KEM. So: make it draft the inventory and the diff; **you** read the before/after handshake
captures yourself and confirm the modern client negotiated the *hybrid* group and the legacy client still
connected. Then ask it: "what would make the modern handshake silently fall back to classical here?" — and
verify each answer against an actual capture, not the model's claim.

## Connects forward
This is the brownfield reality that turns the rest of the track forward-looking. The handshake you migrate
is the one you dissected in **Module 05 (TLS Deep Dive)** — same negotiation, now with a post-quantum group
in it; the *inventory-the-real-handshake* skill is the same one **Module 10 (Auditing Applied-Crypto
Failures)** builds, pointed at a migration instead of an audit. The **hybrid "safe if either holds"**
reasoning is the same risk-hedging judgment **Module 03 (Asymmetric & Key Exchange)** introduced, now
applied under a real deadline. And this lab covers only the *key-exchange* migration (FIPS 203, the
HNDL-urgent one); the **signature** migration to ML-DSA/SLH-DSA (FIPS 204/205) — re-issuing certificates
under a post-quantum signature — is the natural follow-on, on its own slower clock, and the same additive,
prove-interop discipline applies.

## Marketable proof
> "I migrate a TLS service's key exchange from classic ECDHE to a hybrid post-quantum suite
> (`X25519MLKEM768`) without breaking interop — strangler-fig, additive: I inventory what the service
> actually negotiates by reading the handshake (not the config), *add* the hybrid group while keeping the
> classical fallback, and prove the migration with before/after handshake captures that show a modern
> client now negotiates the quantum-safe hybrid path *while a legacy client still connects classically*.
> I can explain harvest-now-decrypt-later, why key exchange (FIPS 203 / ML-KEM) is the urgent migration
> while signatures (FIPS 204/205) follow separately, why hybrid is *safe if either X25519 or ML-KEM holds*,
> and why the proof is the handshake capture — not the config keyword that can silently fall back."

## Stretch
- **Prove the fallback the hard way:** capture the actual `ClientHello`s with `tshark`/Wireshark and show
  the modern client *offers both* `X25519MLKEM768` and `X25519` in its supported_groups while the legacy
  client offers only classical — so the negotiation outcome is visibly *the client's capability*, not a
  server toggle. This makes the strangler-fig mechanism legible on the wire.
- **The ossification gotcha:** ML-KEM `ClientHello`s are large enough to split across packets and trip some
  middleboxes (the "protocol ossification" failure Cloudflare documents). Add a constrained-MTU or a naive
  middlebox to the lab, watch a hybrid handshake fail where classical succeeds, and write the operational
  note — this is the real-world reason PQC rollouts are gradual, not a flag flip.
- **Take the signature migration one step:** re-issue the server certificate under an ML-DSA (FIPS 204)
  signature using OpenSSL 3.5, serve it to a client that supports PQC signatures alongside the RSA cert
  for those that don't, and capture the negotiated signature scheme — proving the *separate* clock the key
  exchange and signature migrations run on.

---

## Lab-env spec (to be built & validated)

*This module has no `plaintext-labs` directory wired yet; build it under
`plaintext-labs/cryptography/11-pqc-migration/` and validate `make up && make demo && make down` on a clean
Linux runner before the module counts as done. It runs entirely in Docker (or against a local OpenSSL
3.5+), with **zero cloud cost and zero third-party provider** when OpenSSL 3.5+ is present. It must
contain:*

- **The brownfield TLS service, in `docker-compose.yml`** — an **nginx** (or OpenSSL `s_server`) container
  terminating TLS 1.2/1.3 with **ECDHE key exchange and an RSA server certificate, no PQC** — the
  classical baseline. Ship a self-signed cert generated at `make up` (gitignored; never commit the key).
- **Two client containers** — a **modern** client built on **OpenSSL 3.5+** (capable of offering
  `X25519MLKEM768` natively; *fallback*: OpenSSL 3.0–3.4 + `oqs-provider` — document which the image uses)
  and a **legacy** client on an older OpenSSL that knows **only classical groups**. Both can `s_client` /
  `curl` the service. The contrast between them *is* the interop proof.
- **The migration mechanism (`make migrate` / `make rollback`)** — `migrate` edits the server config to
  **add** `X25519MLKEM768` *in front of* the retained classical groups and reloads with no downtime;
  `rollback` restores the classical-only group list and reloads. Both idempotent and re-runnable; the
  classical fallback is *always* present except as the explicit big-bang counter-demo.
- **The before/after handshake harness (`handshake-check.sh <host>`)** — the `make verify`/`make demo`
  equivalent and the success signal: asserts (1) the modern client's negotiated group is exactly
  `X25519MLKEM768` (parsed from `s_client` output — *string-match the group, not just handshake success*),
  (2) the legacy client still completes a **classical** handshake, (3) both get a 200. It must **fail
  closed**: a silent classical fallback on the modern client, a connection error, or a timeout counts as a
  **failure**, never a pass. It should *fail before `make migrate`* (modern client on classical) and *pass
  after*.
- **`make inventory`** — runs `s_client`/`testssl.sh` against the service and prints the negotiated
  group/cipher/cert per client (the baseline crypto inventory the learner records).
- **`Makefile`** — `up` / `inventory` / `migrate` / `verify` (alias `demo`) / `rollback` / `shell` / `down`
  (+ a `reset` that returns to the classical-only baseline).
- **CI note:** this is largely CI-runnable (`make up`, `make migrate`, `make verify` green proves the hybrid
  negotiates and the legacy client still connects) — add `.ci-demo` **only once** `make up && make demo &&
  make down` is green on a Linux runner *and* the runner's OpenSSL build genuinely supports
  `X25519MLKEM768` (verify with `openssl s_client -groups X25519MLKEM768` actually negotiating it, since a
  build without ML-KEM is the exact silent-fallback failure this lab teaches). Until validated, leave
  `.ci-demo` off.
