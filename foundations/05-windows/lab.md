# Lab 05 — Triage a Windows Intrusion in the Event Log

*Variant D · skill-first, breach as the stakes. [← Back to the module concept](README.md)*

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/05-windows
make demo   # parse the bundled EVTX-shaped sample + print the PowerShell guide
```

No Docker required — the log analysis runs on macOS/Linux/Windows with Python 3. The bundled
`data/evtx_sample.json` is a small, EVTX-shaped event sample modelling a real Windows intrusion;
`triage.py` is the analysis tool you'll read and extend.

For the optional **live** steps (enumerating local admins, services, Run keys on a real host) you
want a Windows machine you own — a free
[Windows evaluation VM](https://developer.microsoft.com/windows/downloads/virtual-machines/) in
your module-02 lab is ideal. Snapshot it first.

## Scenario
You're the analyst on shift. A workstation has been flagged as "acting strange after a phishing
email," and you've been handed an export of its event log. The behaviour matches a commodity
loader (Emotet-style): it ran something obfuscated, and it wants to survive a reboot. Your job is
to read the log, **name the two attacker moves** — the persistence mechanism and the suspicious
command — and turn that judgment into a check the tool runs for you next time.

> The sample is a log file, not malware — it's safe to open. The live VM steps must run **only**
> on a machine you own. Only ever test systems you own or have explicit written permission to test.

## Do

Each step is **Do** (gather the evidence) → **Verdict** (say what it means, in your own words).

1. [ ] **Get the lay of the log.** Run `make demo` and read the Event ID breakdown. Map each ID to
   what it means (the README table is your key). **Verdict:** which IDs are routine noise, and
   which two are the ones a defender cares about here?

2. [ ] **Find the persistence.** Locate the **7045** event (a new service was installed). Note the
   service name and the image path. **Verdict:** why does a service give an attacker persistence
   that a one-off process doesn't? Name the MITRE technique
   ([T1543.003](https://attack.mitre.org/techniques/T1543/003/)).

3. [ ] **Find the execution — and read what it hid.** Locate the process-creation event (**4688**)
   carrying a PowerShell command launched with `-EncodedCommand`. The argument is base64. Decode it
   (`echo '<blob>' | base64 -d` — remember Windows base64 is UTF-16, so pipe through
   `iconv -f UTF-16LE` if it looks like every-other-character is a dot). **Verdict:** what was the
   command actually doing, and why did the attacker encode it? Name the technique
   ([T1059.001](https://attack.mitre.org/techniques/T1059/001/)).

4. [ ] **Check the registry angle.** Find the Run-key write (**4657**) and connect it to the same
   campaign. **Verdict:** in one sentence, why is `...\CurrentVersion\Run` a persistence location?
   (T1547.001.) *Optional live check:* on your own VM, run
   `Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"` and confirm you can read
   what launches at logon.

5. [ ] **Write the timeline.** Order the events and state, in two or three sentences, the attacker's
   story: initial access → obfuscated execution → persistence (service + Run key). This is your
   `windows-triage.md` deliverable.

## Success criteria — you're done when
- [ ] You can name the **two attacker moves** in the sample by Event ID: the service install
  (7045 → T1543.003) and the encoded PowerShell (4688 → T1059.001).
- [ ] You **decoded** the `-EncodedCommand` blob and can say what it does in plain English.
- [ ] You can explain why a Run-key write (4657 → T1547.001) is persistence.
- [ ] Your extended `triage.py` (below) flags the encoded-PowerShell event automatically and you've
  confirmed it fires on the sample.

## Deliverables
`windows-triage.md` — the two named techniques (with Event IDs), the decoded command, the Run-key
explanation, and a three-sentence attacker timeline. Plus your extended `triage.py`. Commit both.
Do **not** commit any real malware sample, captured `.evtx` from another host, or credentials.

## Automate & own it
**Required — extend the triage tool.** Right now `triage.py` flags logons, scheduled tasks, Run
keys, and service installs, but it does **not** catch encoded PowerShell — the move you just
decoded by hand. Fix that:

1. Add an encoded-PowerShell event to `data/evtx_sample.json`: a **4688** event whose command line
   contains `powershell.exe -EncodedCommand <base64>` (base64-encode a harmless command yourself so
   you know the answer).
2. In `triage.py`, add a check in the analysis pass that flags any 4688 whose command line contains
   `-enc` / `-EncodedCommand`, prints the technique (**T1059.001**), and — bonus — base64-decodes
   the blob inline so the analyst sees the cleartext.
3. Re-run `make demo` and confirm your new check fires.

**AI drafts → you review every line → you own it.** Have a model write the decode-and-flag function,
then read it: does it handle the UTF-16LE encoding Windows uses? Does it fail safely on a blob that
isn't valid base64 (a real log will have both)? Don't ship a line you can't explain. The point isn't
the keystrokes — it's encoding your hand-triage judgment into something the tool does for you.

## AI acceleration
Paste the sample export into a model and ask it to triage it before you do — it will reliably flag
the 7045 and the encoded command. Then audit it: ask it *which Event ID* proves persistence and make
it cite the technique. It's a fast first analyst and a useful adversary; the skill is checking its
verdict against the actual IDs, not trusting it. When you write the decoder, ask it to find a blob
that slips past your check (wrong encoding, lowercase `-enc`) — if one does, your check is too narrow.

## Connects forward
This Windows literacy is assumed by Track 06 (Active Directory — Kerberos and logon events at
scale), Track 07 (endpoint hardening), and Track 03 (forensics — registry and event-log analysis).
Reading a real EVTX and naming techniques by ID is a direct preview of Track 02 detection-as-code,
where these same Event IDs become detection rules. The extended `triage.py` is a seed of the
Foundations capstone's log-parsing tool.

## Marketable proof
> "Given a Windows event-log export, I can triage a commodity-loader intrusion — name the
> persistence mechanism (service install, 7045 → T1543.003) and the obfuscated execution (encoded
> PowerShell, 4688 → T1059.001), decode the payload, and extend a triage tool to catch it next time."

## Stretch
- Pull a **real** `.evtx` from [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)
  (real logs from actual attack techniques), open it with `Get-WinEvent -Path sample.evtx`, and run
  your extended triage logic against an export of it.
- Add a 4104 (PowerShell script-block) check to `triage.py` and explain why 4104 sometimes shows you
  the decoded script when 4688's command line doesn't.
