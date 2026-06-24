# Data provenance — Lab 01 (Telemetry)

## Real dataset: loghub OpenSSH_2k.log

- **Dataset:** loghub — OpenSSH (`OpenSSH_2k.log`)
- **Source URL (verified):** https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log
- **Repository:** https://github.com/logpai/loghub
- **License:** loghub datasets are released for research and educational use (see the loghub repo's
  terms / Zenodo record). Attribute loghub when you reuse the data.
- **What it contains:** 2000 lines of a genuine OpenSSH (`sshd`) authentication log from a host named
  `LabSZ`. It captures real internet brute-force / invalid-user activity from live scanning hosts
  (e.g. `173.234.31.186`, `52.80.34.196`, `202.100.179.208`), including
  `Invalid user … / Failed password / authentication failure` records and
  `POSSIBLE BREAK-IN ATTEMPT` reverse-DNS warnings.
- **How `make fetch-data` retrieves it:** `curl -fsSL <source URL> -o data/OpenSSH_2k.log`.
  Once present, `pipeline.py` consumes `data/OpenSSH_2k.log` automatically (it falls back to the
  committed `ssh_auth.txt` seed when the real log is absent, so `make demo` works offline).

## Committed seed: `ssh_auth.txt`

A trimmed, format-faithful sample (host `LabSZ`, the same real attacker IPs and a handful of benign
`deploy`/`analyst` logins) so the offline `make demo` has data without a network fetch. It is *not*
the real dataset — run `make fetch-data` to analyze the genuine 2000-line loghub log.

## Citation

> Jieming Zhu, Shilin He, Jinyang Liu, Pinjia He, Qi Xie, Zibin Zheng, Michael R. Lyu.
> "Tools and Benchmarks for Automated Log Parsing." ICSE 2019 (SEIP). loghub:
> https://github.com/logpai/loghub
