# Lab 03 — Linux Hardening to CIS

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/03-linux-hardening
make up        # build the container (Lynis + OpenSCAP + SCAP Security Guide)
make demo      # run Lynis audit, then OpenSCAP CIS profile scan, show findings
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally in a container you own. No external targets.

## Scenario

Meridian Financial is rolling out a CIS-hardened Ubuntu 22.04 image for all new Linux application
servers. You have been handed the default Ubuntu 22.04 base image — no hardening applied. Your job:
audit it with Lynis and OpenSCAP, apply a set of CIS Level 1 remediations, and demonstrate a
measurable score improvement to the security team.

## Do

1. [ ] `make demo` — watch both tools run and note the initial Lynis hardening index and the
   OpenSCAP CIS pass percentage. Record both numbers.

2. [ ] `make shell` to enter the container. Run Lynis manually and explore the full output:
   ```bash
   lynis audit system --no-colors 2>&1 | less
   ```
   Find three findings in the `[WARNING]` category. For each one: what is the finding, what
   does Lynis recommend, and which CIS control does it map to?

3. [ ] Run the OpenSCAP CIS Level 1 scan manually and save the results:
   ```bash
   oscap xccdf eval \
     --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
     --results /tmp/results.xml \
     --report /tmp/report.html \
     /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
   oscap info /tmp/results.xml | grep score
   ```
   Open `/tmp/report.html` in a browser if possible, or grep the XML for `fail` rules.

4. [ ] Apply three remediations from the Lynis output. A good starting set:
   - Enable ASLR: `echo "kernel.randomize_va_space=2" >> /etc/sysctl.conf && sysctl -p`
   - Disable ICMP redirects: `sysctl -w net.ipv4.conf.all.accept_redirects=0`
   - Restrict core dumps: `echo "* hard core 0" >> /etc/security/limits.conf`

5. [ ] Re-run both tools after your changes. Did the Lynis hardening index improve? Did the
   OpenSCAP pass count increase? Record the after numbers.

6. [ ] Identify two findings that you *cannot* remediate in a container environment (e.g. kernel
   module loading, filesystem mount options). Document them with the acceptance reason: "Container
   environment — kernel namespace constraint; mitigated by host kernel hardening."

## Success criteria — you're done when

- [ ] You have before/after scores from both Lynis and OpenSCAP.
- [ ] You applied at least three remediations and can explain what each one does.
- [ ] You have two accepted findings with documented rationale.
- [ ] You can explain the difference between a Lynis hardening index and an OpenSCAP CIS score.

## Deliverables

`hardening-log.md` — the before/after scores, the three remediations applied (command + what it
does + which CIS control), and the two accepted findings with rationale. Commit it.

## Automate & own it

**Required.** Write a shell script `audit.sh` that runs both Lynis and OpenSCAP, extracts the
scores from their output, compares them to a minimum threshold (e.g. Lynis ≥ 65, OpenSCAP ≥ 60%),
and exits non-zero if either is below threshold. Have an AI draft the parsing logic (grep/awk for
the score lines); you verify it produces the correct exit code on the sample container before
committing.

## AI acceleration

Paste a failing OpenSCAP rule ID (e.g. `xccdf_org.ssgproject.content_rule_sysctl_net_ipv4_conf_all_accept_redirects`)
into an AI assistant and ask for: what it tests, why it matters, and the one-line fix. Use the
explanation to understand the control before applying the fix. Verify the fix against the SSG
rationale at `https://complianceascode.readthedocs.io/`.

## Connects forward

The sysctl parameters you set here are the foundation for module 04 (Exploit Mitigation) and
module 07 (Compliance Auditing — where you automate the scan and track drift over time). The
accepted findings with documented rationale are exactly the "exception management" process
module 07 formalises.

## Marketable proof

> "I ran CIS-level Linux audits with Lynis and OpenSCAP, applied kernel hardening and configuration
> remediations, and built a threshold-checking audit script that exits non-zero when the score drops."

## Stretch

- Generate the OpenSCAP remediation script (`--fix-type bash --fix /tmp/fix.sh`) and review it
  before running. Which remediations does it apply correctly? Which would you not run in
  production and why?
- Run Lynis with `--auditor "Meridian Security"` and `--log-file /tmp/lynis.log`. Parse the log
  file to extract only WARNING and SUGGESTION lines — this is the foundation of a Lynis-to-SIEM
  pipeline.
