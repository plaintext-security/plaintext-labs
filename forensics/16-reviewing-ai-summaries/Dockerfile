# Reference lab image: an adversarial review harness for AI-drafted incident summaries.
# Pure Python stdlib — the claim-verifier cross-references the summary's structured
# fields against the bundled primary artifacts. No network, no live model.
FROM python:3.12-slim

COPY scripts/ /scripts/
COPY data/ /data/

RUN chmod +x /scripts/*.py 2>/dev/null || true

WORKDIR /lab
