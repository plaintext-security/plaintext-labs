#!/bin/bash
# Samba4 AD DC setup for Corp domain.
# Provisions domain, OUs, users, groups, SPNs, and misconfigurations.
set -e

DOMAIN="CORP"
REALM="CORP.LOCAL"
ADMIN_PASS="C0rp@Admin!"
DC_IP="10.10.0.10"

echo "[*] Provisioning Samba AD DC for ${REALM}..."

samba-tool domain provision \
    --domain="${DOMAIN}" \
    --realm="${REALM}" \
    --adminpass="${ADMIN_PASS}" \
    --server-role=dc \
    --use-rfc2307 \
    --dns-backend=SAMBA_INTERNAL \
    --host-ip="${DC_IP}" \
    --option="dns forwarder = 8.8.8.8" 2>&1 | tail -5

echo "[*] Starting Samba in background..."
samba --daemon

# Wait for samba to be ready
for i in $(seq 1 30); do
    if samba-tool domain info dc01.corp.local >/dev/null 2>&1; then
        echo "[*] Samba ready."
        break
    fi
    sleep 2
done

echo "[*] Creating Organisational Units..."
samba-tool ou create "OU=Corp,DC=corp,DC=local"
samba-tool ou create "OU=Finance,OU=Corp,DC=corp,DC=local"
samba-tool ou create "OU=IT,OU=Corp,DC=corp,DC=local"
samba-tool ou create "OU=HR,OU=Corp,DC=corp,DC=local"
samba-tool ou create "OU=ServiceAccounts,DC=corp,DC=local"

echo "[*] Creating security groups..."
samba-tool group add "IT-Admins" --nis-domain=corp --gid-number=2001
samba-tool group add "IT-Staff" --nis-domain=corp --gid-number=2002
samba-tool group add "Helpdesk-Staff" --nis-domain=corp --gid-number=2003
samba-tool group add "Finance-Users" --nis-domain=corp --gid-number=2004
samba-tool group add "Finance-Managers" --nis-domain=corp --gid-number=2005
samba-tool group add "Payroll-Access" --nis-domain=corp --gid-number=2006
samba-tool group add "HR-Users" --nis-domain=corp --gid-number=2007
samba-tool group add "HR-Managers" --nis-domain=corp --gid-number=2008

echo "[*] Creating Finance users..."
for user in jsmith amurphy bwilson clee dthomas efoster gharris hjohnson ijones jkim klopes lmartin mnguyen npark; do
    samba-tool user create "${user}" "Welcome1!" \
        --userou="OU=Finance,OU=Corp,DC=corp,DC=local" \
        --given-name="${user}" --surname="Corp" 2>/dev/null || true
    samba-tool group addmembers "Finance-Users" "${user}"
done
samba-tool group addmembers "Finance-Managers" "amurphy"
samba-tool group addmembers "Payroll-Access" "clee"

echo "[*] Creating IT users..."
samba-tool user create "tallen" "T@ll3n_IT@dmin!" \
    --userou="OU=IT,OU=Corp,DC=corp,DC=local" 2>/dev/null || true
samba-tool group addmembers "Domain Admins" "tallen"
samba-tool group addmembers "IT-Admins" "tallen"

for user in sgarcia rrodriguez pmartinez qwalker ubrown vdavis; do
    samba-tool user create "${user}" "Welcome1!" \
        --userou="OU=IT,OU=Corp,DC=corp,DC=local" 2>/dev/null || true
done
samba-tool group addmembers "IT-Admins" "sgarcia"
samba-tool group addmembers "IT-Admins" "pmartinez"
samba-tool group addmembers "Helpdesk-Staff" "rrodriguez"
samba-tool group addmembers "Helpdesk-Staff" "qwalker"
samba-tool group addmembers "IT-Staff" "ubrown"
samba-tool group addmembers "IT-Staff" "vdavis"

echo "[*] Creating HR users..."
for user in wevans xtaylor yadams zclark abaker bscott chill dmitchell ewhite; do
    samba-tool user create "${user}" "Welcome1!" \
        --userou="OU=HR,OU=Corp,DC=corp,DC=local" 2>/dev/null || true
    samba-tool group addmembers "HR-Users" "${user}"
done
samba-tool group addmembers "HR-Managers" "wevans"

echo "[*] Creating service accounts with SPNs (Kerberoastable)..."
samba-tool user create "svc-mssql" "Sql$3rv1ce2019!" \
    --userou="OU=ServiceAccounts,DC=corp,DC=local" 2>/dev/null || true
samba-tool spn add "MSSQLSvc/db01.corp.local:1433" "svc-mssql"

samba-tool user create "svc-backup" "B@ckup$3rv1ce!" \
    --userou="OU=ServiceAccounts,DC=corp,DC=local" 2>/dev/null || true
samba-tool spn add "BackupSvc/backup01.corp.local" "svc-backup"
samba-tool group addmembers "Backup Operators" "svc-backup" 2>/dev/null || true

samba-tool user create "svc-web" "W3b$3rv1ce2021!" \
    --userou="OU=ServiceAccounts,DC=corp,DC=local" 2>/dev/null || true
samba-tool spn add "HTTP/intranet.corp.local" "svc-web"

echo "[*] Creating AS-REP roastable service accounts (no pre-auth)..."
samba-tool user create "svc-legacy" "L3g@cy$3rv1ce!" \
    --userou="OU=ServiceAccounts,DC=corp,DC=local" 2>/dev/null || true
# Set DONT_REQUIRE_PREAUTH flag (userAccountControl 4194304)
samba-tool user setexpiry svc-legacy --noexpiry
python3 /data/set_nopreauth.py "svc-legacy" 2>/dev/null || \
    ldbmodify -H /var/lib/samba/private/sam.ldb /data/svc-legacy-nopreauth.ldif 2>/dev/null || true

samba-tool user create "svc-monitor" "M0n1t0r$3rv1ce!" \
    --userou="OU=ServiceAccounts,DC=corp,DC=local" 2>/dev/null || true

echo "[*] Creating svc-deploy (member of IT-Admins — GenericWrite misconfiguration)..."
samba-tool user create "svc-deploy" "D3pl0y$3rv1ce!" \
    --userou="OU=ServiceAccounts,DC=corp,DC=local" 2>/dev/null || true
samba-tool group addmembers "IT-Admins" "svc-deploy"

echo "[*] Domain provisioning complete."
echo "    Domain:      ${REALM}"
echo "    Admin:       Administrator / ${ADMIN_PASS}"
echo "    Test user:   jsmith / Welcome1!"
echo "    LDAP port:   389"
echo "    Kerberos:    88"

# Keep the container alive
exec samba --foreground --no-process-group
