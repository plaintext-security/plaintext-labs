#!/usr/bin/env python3
"""Set DONT_REQUIRE_PREAUTH on a Samba4 user via ldb."""
import sys
import subprocess

if len(sys.argv) < 2:
    print("Usage: set_nopreauth.py <username>")
    sys.exit(1)

username = sys.argv[1]
sam_db = "/var/lib/samba/private/sam.ldb"

# Get current userAccountControl
result = subprocess.run(
    ["ldbsearch", "-H", sam_db, f"(sAMAccountName={username})", "userAccountControl"],
    capture_output=True, text=True
)

uac = 512  # default normal account
for line in result.stdout.splitlines():
    if line.startswith("userAccountControl:"):
        uac = int(line.split(":")[1].strip())
        break

# Set DONT_REQUIRE_PREAUTH (0x400000 = 4194304)
new_uac = uac | 4194304

ldif = f"""dn: CN={username},OU=ServiceAccounts,DC=corp,DC=local
changetype: modify
replace: userAccountControl
userAccountControl: {new_uac}
"""

proc = subprocess.run(
    ["ldbmodify", "-H", sam_db],
    input=ldif, capture_output=True, text=True
)
if proc.returncode == 0:
    print(f"[+] DONT_REQUIRE_PREAUTH set on {username} (UAC={new_uac})")
else:
    print(f"[-] Failed: {proc.stderr}")
    sys.exit(1)
