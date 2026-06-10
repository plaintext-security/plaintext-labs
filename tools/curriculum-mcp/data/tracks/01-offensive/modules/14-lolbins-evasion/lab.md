# Lab 14 — Live Off the Land (LOLBins)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/14-lolbins-evasion
make up
```

The container has Debian with `python3`, `curl`, `wget`, `crontab`, and `bash` —
the native binaries used in the LOLBin chain. A benign stage-2 payload lives in
`payload/stage2.py`.

## Scenario

You have a shell on a Meridian Financial server. The endpoint has an EDR that
blocks known-malicious binaries but allows native tools. Accomplish your
objectives — download a payload, execute it, and persist — using only the
system's own trusted binaries.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Build the download→exec→persist chain yourself using only native binaries, before
   watching the worked run. Stand up a local payload server, pull `stage2.py` down with a
   trusted interpreter instead of a flagged downloader, execute it without dropping a
   recognisable binary, and persist via a native scheduler. (Which interpreter already
   present can fetch a URL? Which can run code straight from a file or string?) `make demo`
   runs the validated chain — use it afterwards to check which binary you used per step.

2. [ ] Read `lolbins_demo.py` and explain why each step evades signature-based blocking:
   - How does the chosen interpreter replace a dedicated downloader like `curl`?
   - What makes executing code read from a file evade binary signatures?
   - How does piping into the scheduler avoid writing a flagged file under `/etc/cron.d`?

3. [ ] For each detection artifact the chain leaves:
   - Write the auditd rule that would catch the download (an interpreter opening a TCP socket)
   - Write the osquery query that would find the crontab entry writing to /tmp

4. [ ] Read the Windows LOLBAS table the lab ships. For each Windows binary:
   - Look up the entry on [LOLBAS](https://lolbas-project.github.io/)
   - What is its normal purpose? What makes the malicious use hard to block?

## Success criteria — you're done when

- [ ] You traced the download→exec→persist chain in `lolbins_demo.py` step by step.
- [ ] You can explain what each native binary is *supposed* to do and why it's trusted.
- [ ] You can describe the behavioural detection that catches each step.
- [ ] You ran the download cradle manually and confirmed the payload executed.

## Deliverables

`lolbins.md`: the binaries used for each step (Linux + Windows), the detection
artifact that each generates, and the query/rule you'd write to catch it.

## Automate & own it

**Required.** Write `lolbins_chain.sh` that:
- Takes a payload URL and a drop path as arguments
- Implements the full download→exec→persist chain in a single script
- Uses only native binaries (no curl if python3 is available, etc.)

AI drafts the script; you trace each step and verify the auditd events.
Commit `lolbins_chain.sh` and `lolbins.md`.

## AI acceleration

Ask a model to generate YARA rules or Sigma rules that would detect
`exec(open(PATH).read())` patterns in Python process arguments. Then test
the rule logic against the actual command line from `make demo`.

## Connects forward

LOLBins are the operational layer for any post-exploitation in module 13
(C2) and Track 06 (AD). The defensive inverse is Track 02, module 11
(hunting-endpoint) — the Sysmon/osquery queries from that module would
detect the crontab and process-chain artifacts here.

## Marketable proof

> "I can execute a full LOLBin chain on Linux using only native interpreters,
> and I can write the behavioural detection rules that catch it anyway."

## Stretch

- Add a Windows LOLBin demo: on your eval VM, execute the `powershell` download
  cradle and `certutil` chain from Step 5. Observe in Sysmon Event ID 1 (process
  creation) and Event ID 3 (network connection).
- Modify `lolbins_demo.py` to add a jitter to the download timing. Does this
  affect the detection window?
