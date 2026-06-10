# Lab 09 — Local Privilege-Escalation Defense

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/09-privesc-defense
make up        # build the container with a deliberate SUID misconfiguration
make demo      # show find discovering the SUID binary, demonstrate the privesc path
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally in a container you own. The misconfiguration is deliberate and
> contained to the lab environment.

## Scenario

Meridian Financial's red team reported that the payroll server has at least one exploitable
SUID binary misconfiguration. Before the remediation window, your job is to: verify the
finding, understand the exploitation path, apply the remediation, confirm the path is closed,
and add the check to the compliance scan so it doesn't regress.

## Do

1. [ ] `make demo` — observe the SUID binary being found with `find / -perm -4000`. Note which
   binary it is. Look it up on [GTFOBins](https://gtfobins.org/) — what escalation
   technique does it enable?

2. [ ] `make shell` (as the low-privileged `appuser`) and attempt the GTFOBins technique:
   ```bash
   # As appuser — verify you are not root:
   id
   whoami
   # Now use the misconfigured SUID binary (see make demo output for the path)
   # Follow the GTFOBins SUID technique for that binary
   ```
   Did you reach root? Document the exact commands and the output.

3. [ ] Remediate: remove the SUID bit from the binary:
   ```bash
   # Switch to root (or use sudo):
   chmod u-s /path/to/binary
   ls -la /path/to/binary   # confirm the 's' bit is gone
   ```
   Re-attempt the GTFOBins technique as `appuser`. Confirm it fails.

4. [ ] Add the AppArmor second layer: load the AppArmor profile from `data/suid-apparmor-profile`
   and confirm it is in enforce mode:
   ```bash
   apparmor_parser -r /lab/data/suid-apparmor-profile
   aa-status | grep -A2 meridian
   ```
   Re-attempt the escalation and observe both the permission denial and the AppArmor log entry.

5. [ ] Audit the full SUID set on the container:
   ```bash
   find / -perm -4000 -type f 2>/dev/null
   ```
   Cross-reference every result against GTFOBins. Document which ones are dangerous, which are
   expected (e.g. `sudo` itself), and which you would remove in a production hardening run.

6. [ ] Write an osquery query that finds SUID binaries continuously:
   ```sql
   SELECT path, permissions, uid, gid
   FROM file
   WHERE path LIKE '/usr/%'
   AND permissions LIKE '%s%'
   AND uid = 0;
   ```
   Add this query to `data/queries.sql` from module 05.

## Success criteria — you're done when

- [ ] You demonstrated the SUID privesc path as `appuser`.
- [ ] You remediated it (removed SUID bit) and confirmed the path is closed.
- [ ] You added AppArmor as a second layer and observed the denial log.
- [ ] You audited the full SUID set and documented which binaries are dangerous.
- [ ] You have an osquery query that would detect a new SUID binary being added.

## Deliverables

`privesc-audit.md` — the full SUID binary audit table (binary, is dangerous per GTFOBins,
action taken: remove/keep/profile). Commit it. Also commit the updated `queries.sql` with
the SUID detection query.

## Automate & own it

**Required.** Write a shell script `suid-audit.sh` that: runs `find / -perm -4000 2>/dev/null`,
downloads (or reads from local cache) the GTFOBins binary list, and flags any SUID binary
that matches a GTFOBins entry. Output: "DANGEROUS: /path/to/binary (GTFOBins technique: X)"
or "OK: /path/to/binary". Have an AI draft the comparison logic; you verify it against a known
list before committing.

## AI acceleration

After finding the SUID binary with `find`, paste its name into an AI and ask: "What is the
GTFOBins SUID technique for this binary? Walk me through the exact commands." Then verify the
technique against [gtfobins.org](https://gtfobins.org/) — the model may have the
technique slightly wrong or may suggest a newer variant. Run the technique in the lab to confirm
it actually works before writing the remediation documentation.

## Connects forward

The osquery SUID query you wrote here feeds module 10 (detecting host compromise) — a new SUID
binary added to a production host is a detection signal. The AppArmor confinement from module 04
and this module work together as the dual-layer defense that the track capstone integrates.

## Marketable proof

> "I identified a SUID privilege-escalation path using GTFOBins, exploited it in a controlled
> environment to confirm the finding, remediated with permission hardening and AppArmor
> confinement, and added an osquery detection query to prevent regression."

## Stretch

- Audit the container's sudo configuration: `cat /etc/sudoers` and `ls /etc/sudoers.d/`. Are
  there any `NOPASSWD` rules? What binaries are granted? Cross-reference with GTFOBins sudo
  techniques.
- Use `getcap -r / 2>/dev/null` to enumerate Linux capabilities. Linux capabilities are the
  "SUID with less blast radius" mechanism — but misconfigured capabilities can also enable
  privilege escalation. Look up `cap_setuid` and `cap_sys_ptrace` on GTFOBins.
