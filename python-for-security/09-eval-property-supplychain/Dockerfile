FROM python:3.12-slim

# hypothesis for property tests + pytest for the gates. The eval harness is plain
# code (the pattern pydantic-evals formalizes); pip-audit is the learner's live
# supply-chain step (needs network) — here the supply-chain gate is an offline
# lockfile-hash check.
RUN pip install --no-cache-dir "pydantic==2.*" "hypothesis==6.*" "pytest==8.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
