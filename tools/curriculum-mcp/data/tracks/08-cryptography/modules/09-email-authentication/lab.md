# Lab 09 — Email Authentication

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/09-email-authentication
make up        # start a local bind9 container seeded with meridian-fictional.com records
make demo      # query SPF, DKIM, DMARC; validate; show what each record does
make shell     # drop into the dig/openssl container
make down      # stop when done
```

> Everything runs locally against a seeded local DNS server. No external DNS queries required.

## Scenario

Meridian Financial's CISO has asked for an email authentication audit. You have been given
the DNS configuration for the fictional domain `meridian-fictional.com`. Your job: query and
validate all three records (SPF, DKIM, DMARC), identify any misconfigurations, and produce a
remediation recommendation with corrected records.

## Do

1. [ ] `make demo` — watch all three records queried and validated. Note the policy in the
   DMARC record: is it `none`, `quarantine`, or `reject`? Is there a DKIM selector configured?

2. [ ] `make shell` and query all three records yourself against the local resolver with `dig`
   (the DKIM selector is in `data/dns-records.txt`; recall the `_dmarc.` and
   `<selector>._domainkey.` prefixes the protocols use). For each record note the full TXT
   value, what each field means, and whether it is complete and well-formed.

3. [ ] Validate the SPF record:
   - Does the SPF record end with `~all` (softfail) or `-all` (hardfail)? What is the
     security difference?
   - How many DNS lookups does the SPF record require? (Each `include:` and `a:` mechanism
     adds one; SPF has a 10-lookup limit.)
   - Write the corrected SPF record with `-all` if the existing one uses `~all`.

4. [ ] Validate the DKIM public key: extract the `p=` value from the DKIM TXT record, base64-
   decode it, and inspect it with OpenSSL. What key type and size is it — RSA-2048 or larger?
   Ed25519? Is it strong enough?

5. [ ] Validate the DMARC record:
   - What is the `p=` policy? (none / quarantine / reject)
   - Is there an `rua=` (aggregate report) address? If not, the domain owner is flying blind.
   - Is `adkim=s` (strict alignment) set? What is the security difference between strict and
     relaxed DKIM alignment?
   - Write the corrected DMARC record with `p=reject`, `adkim=s`, and an `rua=` address.

6. [ ] Write `email-auth-audit.md`: a finding-per-row table for the three records, with
   columns: record type, current value, finding (misconfiguration or missing field), severity
   (HIGH/MEDIUM/LOW), and recommended corrected value.

## Success criteria — you're done when

- [ ] You queried all three records and identified the policy weakness in each.
- [ ] You decoded the DKIM public key and noted the key type and size.
- [ ] You produced corrected records for SPF (`-all`) and DMARC (`p=reject`, `adkim=s`, `rua=`).
- [ ] You produced a structured audit finding table.

## Deliverables

`email-auth-audit.md` — your audit finding table with corrected records. Commit it.

## Automate & own it

**Required.** Write a Python script `validate-email-auth.py` that: takes a domain name as
argument, queries the SPF, DKIM (with a configured selector), and DMARC records using Python's
`dnspython` library, and outputs a one-line assessment for each: PASS / WARN (softfail SPF,
none DMARC policy) / FAIL (missing record, syntax error). Have an AI draft the DNS query code;
you verify the WARN and FAIL conditions are correct by testing against the local DNS container.

## AI acceleration

Ask an AI to write the optimal SPF, DKIM (RSA-2048), and DMARC records for a domain with
two authorised sending IPs (one on-premise mail server, one SendGrid). Then validate the
generated records against the RFC syntax checkers in `data/dns-records.txt` and confirm they
match the format of the correctly configured records. AI generates the record values; you
validate the format and test against the local DNS.

## Connects forward

The DMARC `rua=` reporting you configured here produces aggregate reports — the data source
for a threat-intelligence module that analyses spoofing attempts against your domain. The
email authentication audit pattern (query, parse, validate, report) is reused in module 10's
applied-crypto audit workflow.

## Marketable proof

> "I audited SPF, DKIM, and DMARC records for a domain, identified policy weaknesses (softfail
> SPF, none DMARC), produced corrected records, and automated the validation check with a
> Python script that exits non-zero on misconfiguration."

## Stretch

- Research BIMI (Brand Indicators for Message Identification): what does it require beyond
  DMARC `p=reject`, and what does it provide to email recipients? Is BIMI appropriate for a
  company that does not want its logo appearing in competitor emails spoofed as the sender?
- Use `opendkim-testkey` (if available) or OpenSSL to verify that the private key matching the
  DKIM public key in DNS is correct — this is the check that confirms the DKIM signing key
  hasn't been rotated without updating the DNS record.
