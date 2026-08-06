#!/usr/bin/env python3
"""Make Prowler 4.x usable against a local AWS emulator (floci).

Prowler builds its *service* clients with no explicit ``endpoint_url`` (so they
already fall back to the ``AWS_ENDPOINT_URL`` env var that boto3 honours), but
its credential-validation step hardcodes the real public STS endpoint:

    sts_endpoint_url = f"https://sts.{aws_region}.amazonaws.com"

That hardcoded URL overrides the env var, so ``get_caller_identity`` always hits
real AWS and dies with ``InvalidClientTokenId`` before a single check runs —
which is why scoping the scan to fewer services never fixed the lab.

This patch makes ``create_sts_session`` honour ``AWS_ENDPOINT_URL`` when set, so
STS validation (and therefore the whole scan) is routed at the local emulator (floci). It is a
minimal, idempotent in-place edit applied at image build time. Pinned to the
exact source shipped by prowler==4.3.5; if that anchor ever changes the build
fails loudly rather than silently skipping the patch.
"""
import os
import sys

import prowler

target = os.path.join(
    os.path.dirname(prowler.__file__), "providers", "aws", "aws_provider.py"
)

src = open(target, encoding="utf-8").read()

anchor = (
    '        sts_endpoint_url = (\n'
    '            f"https://sts.{aws_region}.amazonaws.com"\n'
    '            if "cn-" not in aws_region\n'
    '            else f"https://sts.{aws_region}.amazonaws.com.cn"\n'
    '        )'
)

replacement = (
    '        # Lab patch: honour AWS_ENDPOINT_URL so STS validation can target\n'
    '        # a local AWS emulator instead of the hardcoded public AWS STS endpoint.\n'
    '        import os as _os\n'
    '        _ep = _os.environ.get("AWS_ENDPOINT_URL")\n'
    '        sts_endpoint_url = _ep if _ep else (\n'
    '            f"https://sts.{aws_region}.amazonaws.com"\n'
    '            if "cn-" not in aws_region\n'
    '            else f"https://sts.{aws_region}.amazonaws.com.cn"\n'
    '        )'
)

if replacement.splitlines()[3] in src:
    print("patch-prowler-endpoint: already applied")
    sys.exit(0)

if anchor not in src:
    sys.exit(
        "patch-prowler-endpoint: STS anchor not found — prowler version drift; "
        "review providers/aws/aws_provider.py create_sts_session()"
    )

open(target, "w", encoding="utf-8").write(src.replace(anchor, replacement))
print(f"patch-prowler-endpoint: patched {target}")
