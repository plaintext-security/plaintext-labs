# Lab 03 — Asymmetric & Key Exchange

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/03-asymmetric-key-exchange
make up        # build the OpenSSL container
make demo      # generate RSA + EC keypairs, sign, verify, ECDH exchange
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs offline. No external dependencies.

## Scenario

Meridian Financial is migrating its internal code-signing infrastructure from RSA-2048 to
ECDSA P-256. Before the cutover, your job is to: generate both keypair types, sign a test
artefact with each, verify the signatures, measure the performance difference, and confirm
the new ECDH key exchange produces identical shared secrets on both sides.

## Do

1. [ ] `make demo` — observe the full sequence: RSA-2048 keygen, ECDSA P-256 keygen, sign, verify,
   ECDH exchange. Note the time taken for each operation.

2. [ ] `make shell` and generate the two keypairs yourself with `openssl genpkey` — an
   RSA-2048 pair and an EC P-256 pair — timing each generation and recording the private-key
   file sizes. Document the generation-time and key-size differences.

3. [ ] Sign a test message with each private key and verify with the matching public key
   (`openssl pkeyutl -sign` / `-verify`). Then tamper with the message and confirm verification
   fails for both.

4. [ ] Perform an X25519 ECDH exchange between two simulated parties. Generate an X25519
   keypair for each:
   ```bash
   openssl genpkey -algorithm X25519 -out /tmp/alice-priv.pem
   openssl pkey -in /tmp/alice-priv.pem -pubout -out /tmp/alice-pub.pem
   # …and the same for Bob.

   # Alice computes shared secret using her private key + Bob's public key:
   openssl pkeyutl -derive -inkey /tmp/alice-priv.pem -peerkey /tmp/bob-pub.pem \
     | xxd | head -2
   # Bob does the same with his private key + Alice's public key.
   ```
   Confirm both sides arrive at the identical secret, and state which property of
   Diffie-Hellman this demonstrates.

5. [ ] Write a brief comparison in `key-exchange-analysis.md`:
   - RSA-2048 vs EC P-256: keygen time, signature size, verify time (measure each).
   - Why X25519 was chosen for the ECDH exchange (vs P-256 ECDH).
   - What "forward secrecy" means for this key exchange and what would break it.

## Success criteria — you're done when

- [ ] You generated RSA-2048 and ECDSA P-256 keypairs and measured the performance difference.
- [ ] You signed and verified a message with each, and confirmed tampering breaks verification.
- [ ] You performed an X25519 ECDH exchange and confirmed Alice and Bob compute the same secret.
- [ ] You can explain why the shared secret is never transmitted.

## Deliverables

`key-exchange-analysis.md` — your comparison table (keygen time, key size, signature size,
verify time) and forward secrecy explanation. Commit it.

## Automate & own it

**Required.** Write a Python script `keygen-benchmark.py` that generates one RSA-2048 and one
EC P-256 keypair 10 times each, times each operation, and prints a comparison table (mean,
min, max for each). Have an AI draft the timing loop using `cryptography.hazmat.primitives.asymmetric`;
you verify the benchmark is fair (same data, same measurement approach) before committing.

## AI acceleration

Ask an AI: "Why is X25519 preferred over P-256 ECDH for key exchange in modern protocols?"
Use the answer to write the "why X25519" paragraph in your `key-exchange-analysis.md`.
Then verify the claims against the [SafeCurves project](https://safecurves.cr.yp.to/) — which
curves does it consider safe, and is P-256 listed? Is X25519?

## Connects forward

The keypair generation and signing you practiced here are the building blocks of the PKI chain
you'll build in module 06 (PKI & Certificate Management). The ECDH exchange is exactly what
TLS 1.3's handshake does in module 05 — understanding the mechanism makes the TLS deep-dive
much clearer.

## Marketable proof

> "I generated RSA and EC keypairs, benchmarked their performance, performed an X25519 ECDH key
> exchange to produce a verified shared secret, and documented the forward secrecy properties
> for Meridian's code-signing migration."

## Stretch

- Generate an Ed25519 keypair (not X25519 — Ed is for signing, X is for key exchange) and
  compare it to ECDSA P-256. Are the signatures deterministic? Why does Ed25519 use
  deterministic signing while ECDSA requires a random nonce?
- Research what happens if the ECDSA signing nonce (k) is reused or predictable. This is the
  Sony PlayStation 3 private key leak — look it up and write a one-paragraph explanation.
