#!/usr/bin/env python3
"""
mint_oidc_token.py — stand in for a CI platform's OIDC provider.

A real CI runner (GitHub Actions, GitLab) mints a short-lived JWT at job time that
*describes this run*: who issued it (iss), who it's for (aud), and the exact
repo/branch (sub). It signs that JWT with the platform's private key and publishes
the matching public key at a JWKS endpoint so AWS STS can verify the signature.

This script does the same thing locally so the OIDC flow is legible end-to-end:
  1. generate (once) an RSA keypair  -> data/oidc/private.pem
  2. publish the public half as a JWKS -> data/oidc/jwks.json  (served by `make jwks`)
  3. mint an RS256-signed JWT with the requested iss/aud/sub claims, short expiry

Usage:
  python mint_oidc_token.py                      # default claims (the intended pipeline)
  python mint_oidc_token.py --sub repo:meridian/api:ref:refs/heads/feature/x
  python mint_oidc_token.py --aud wrong-audience # to test the trust-policy scope

The token is printed to stdout (the pipeline pipes it to AssumeRoleWithWebIdentity).
The private key NEVER leaves this lab and is gitignored — it is not a stored *cloud*
credential, it is the OIDC provider's signing key (the CI platform holds the AWS-side
equivalent, not you).
"""
import argparse
import json
import os
import time

import jwt  # PyJWT
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

HERE = os.path.dirname(os.path.abspath(__file__))
OIDC_DIR = os.path.join(HERE, "oidc")
PRIV = os.path.join(OIDC_DIR, "private.pem")
JWKS = os.path.join(OIDC_DIR, "jwks.json")

# The "intended" pipeline identity — mirrors a GitHub Actions OIDC subject:
#   repo:<org>/<repo>:ref:refs/heads/<branch>
DEFAULT_ISS = "http://oidc-provider:8080"   # our local issuer (served by `make jwks`)
DEFAULT_AUD = "sts.amazonaws.com"
DEFAULT_SUB = "repo:meridian/api:ref:refs/heads/main"
KID = "lab-oidc-key-1"


def _b64url_uint(n: int) -> str:
    import base64
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def ensure_keypair():
    """Generate the signing keypair + JWKS once; reuse on later runs."""
    os.makedirs(OIDC_DIR, exist_ok=True)
    if os.path.exists(PRIV) and os.path.exists(JWKS):
        return
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with open(PRIV, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    pub = key.public_key().public_numbers()
    jwks = {
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": KID,
            "n": _b64url_uint(pub.n),
            "e": _b64url_uint(pub.e),
        }]
    }
    with open(JWKS, "w") as f:
        json.dump(jwks, f, indent=2)


def mint(iss: str, aud: str, sub: str, ttl: int) -> str:
    with open(PRIV, "rb") as f:
        priv = f.read()
    now = int(time.time())
    claims = {
        "iss": iss,
        "aud": aud,
        "sub": sub,
        "iat": now,
        "nbf": now,
        "exp": now + ttl,
        # GitHub-style context claims a strict trust policy could also condition on:
        "repository": "meridian/api",
        "ref": "refs/heads/main",
        "workflow": "deploy",
    }
    return jwt.encode(claims, priv, algorithm="RS256", headers={"kid": KID})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iss", default=DEFAULT_ISS)
    ap.add_argument("--aud", default=DEFAULT_AUD)
    ap.add_argument("--sub", default=DEFAULT_SUB)
    ap.add_argument("--ttl", type=int, default=300, help="token lifetime in seconds")
    args = ap.parse_args()

    ensure_keypair()
    token = mint(args.iss, args.aud, args.sub, args.ttl)
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
