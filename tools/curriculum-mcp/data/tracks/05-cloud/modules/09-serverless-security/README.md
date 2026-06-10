# Module 09 — Serverless Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *serverless doesn't eliminate the attack surface — it moves it into IAM, event triggers, and the runtime environment.*

## Why this matters
Serverless functions run your code in someone else's managed container — you own the code and the
execution role, not the host. That shift transfers OS-level risk to the cloud provider while
concentrating attacker interest on IAM privileges, event injection, and data exfiltration via
environment variables. These are different failure modes than traditional compute, and they require
different tools and a different mental model to audit.

## Objective
Deploy a deliberately vulnerable Lambda function to LocalStack, enumerate its execution role with
`cloudfox`, identify the privilege-escalation path and injection point, and demonstrate the fix as
both a code change and an IAM policy correction.

## The core idea

Serverless architectures make a specific trade with security: you get no OS to patch and no server
to harden, but you accept the cloud provider's trust boundary as your perimeter. The interesting
attack surface is what you control — the execution role, the event input, and the runtime
environment. Each of these maps to a well-documented attack class that practitioners encounter in
real AWS environments.

The execution role is the most common misconfiguration. Lambda functions are frequently created
with `AdministratorAccess` because it's easy and "we'll tighten it later." When an attacker
achieves code execution inside a Lambda (via event injection, a vulnerable dependency, or a
compromised deployment) they inherit that role — and they can use it to create IAM users,
exfiltrate S3 data, spin up EC2 instances for mining, or pivot to any other service the role
allows. The blast radius of an overprivileged execution role is the blast radius of the account.
`cloudfox` was built specifically to automate the discovery of these paths: give it a role ARN and
it tells you what the role can do, what it can escalate to, and what sensitive resources it can
reach.

Event injection is the serverless analogue of SQL injection. A Lambda triggered by an API Gateway
event, an SQS message, or an S3 notification receives a JSON payload that an attacker can control.
If the function passes event fields to a shell command, a database query, or a subprocess without
sanitisation, an attacker who controls the event source controls the execution. In a real
deployment, the event source is often partially trusted (an API Gateway with authentication), but
the Lambda code frequently assumes the input is safe and passes it directly — a classic confused-
deputy pattern.

Environment variables are the standard mechanism for passing configuration to a Lambda — database
connection strings, API keys, internal service endpoints. What makes them interesting from an
attacker's perspective: if you achieve code execution inside the Lambda (by any means), you can
read all environment variables in a single call. This is why the best practice is to store
sensitive configuration in Vault or AWS Secrets Manager and retrieve it at runtime via an API call
rather than loading it into the environment at deploy time. A credential in an environment variable
has a blast radius of "whenever the Lambda runs"; a credential retrieved from Secrets Manager has
a blast radius of "one call, with a CloudTrail record."

The confused deputy problem in serverless adds one more wrinkle: a Lambda with an overprivileged
role that is triggered by an event from an untrusted source is effectively a proxy for privilege
escalation. The attacker's event causes the Lambda to take actions with the Lambda's role — actions
the attacker couldn't take directly. This is MITRE ATT&CK T1548 (Abuse Elevation Control Mechanism)
at the cloud layer, and it is the reason trust boundaries around event sources matter as much as the
role permissions themselves.

## Learn (~4 hrs)

**Serverless attack patterns (~1.5 hrs)**
- [OWASP Serverless Top 10](https://owasp.org/www-project-serverless-top-10/) — the canonical reference for serverless-specific vulnerabilities. Read all ten items; items 1 (Function Event-Data Injection), 2 (Broken Authentication), and 4 (Over-Privileged Function Permissions) are directly covered in this lab.
- [MITRE ATT&CK T1548.005 — Temporary Elevated Cloud Access](https://attack.mitre.org/techniques/T1548/005/) — the confused-deputy and role-chaining techniques in cloud environments.

**cloudfox (~1 hr)**
- [cloudfox — BishopFox/cloudfox](https://github.com/BishopFox/cloudfox) — the tool purpose-built for "find exploitable paths in a cloud account." Read the README, the `aws` command family, and specifically the `permissions`, `role-trusts`, and `env` subcommands. This is your primary tool in the lab.

**Lambda hardening (~1.5 hrs)**
- [AWS Lambda — security best practices](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html) — the official guide: execution role least privilege, VPC placement, environment variable encryption, and resource-based policies. Read all sections.
- [AWS SAM CLI — getting started](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/) — the deployment tool you'll use in the lab. Skim the overview and the `sam deploy` flow; you don't need deep SAM knowledge for this lab.
- [pacu — RhinoSecurityLabs/pacu](https://github.com/RhinoSecurityLabs/pacu) — the AWS exploitation framework. Read the Lambda-specific module list. You won't use it directly in this lab but it contextualises the automated exploitation that cloudfox's findings enable.

## Key concepts
- Lambda execution role: IAM permissions the function has at runtime
- Event injection: untrusted event fields passed to shell/SQL/subprocess without sanitisation
- Confused deputy: Lambda with elevated role triggered by untrusted event source
- Environment variable exfiltration: retrieving all env vars with one API call post-compromise
- cloudfox: permission enumeration, role trust discovery, environment variable harvesting
- MITRE ATT&CK T1078 (Valid Accounts), T1552.005 (Cloud Instance Metadata API), T1548

## AI acceleration
`cloudfox` output is structured JSON — an excellent AI input. Paste the permissions output for a
role and ask the model to identify the highest-impact privilege paths: what can an attacker do from
this role, in what order, to reach account compromise? The model is good at this graph traversal
framing. What it requires from you: confirming that the permissions it identifies actually exist in
the current IAM state (not just that they exist in the policy — detached policies, permission
boundaries, and SCPs can restrict effective permissions), and that any suggested remediation
preserves the function's legitimate use case. The fix must be the *minimum necessary* permissions,
which only you know from the application requirements.
