#!/bin/bash
# Samba4 AD DC setup for Corp domain.
# Provisions domain, OUs, users, groups, SPNs, and misconfigurations.
set -e

DOMAIN="CORP"
REALM="CORP.LOCAL"
ADMIN_PASS="C0rp@Admin!"
DC_IP="10.10.0.10"

echo "[*] Provisioning Samba AD DC for ${REALM}..."

# Store the sysvol ACLs in a tdb (xattr_tdb) instead of real filesystem xattrs.
# Docker's overlayfs rejects the security.NTACL xattr, so the default sysvol ACL
# step fails ("set_nt_acl ... NT_STATUS_ACCESS_DENIED") and aborts provisioning,
# leaving secrets.ldb incomplete so the DC never starts. The tdb backend makes
# provisioning work on any filesystem.
samba-tool domain provision \
    --domain="${DOMAIN}" \
    --realm="${REALM}" \
    --adminpass="${ADMIN_PASS}" \
    --server-role=dc \
    --use-rfc2307 \
    --dns-backend=SAMBA_INTERNAL \
    --host-ip="${DC_IP}" \
    --option="dns forwarder = 8.8.8.8" \
    --option="vfs objects = acl_xattr xattr_tdb" \
    --option="xattr_tdb:file = /var/lib/samba/private/xattr.tdb" 2>&1 | tail -5

# Allow plain LDAP simple binds (port 389) without TLS. Samba 4.17 defaults to
# "ldap server require strong auth = yes", which rejects the ldapsearch -x simple
# binds the labs use ("ldap_bind: Strong(er) authentication required"). This is an
# intentionally permissive teaching DC — the lab enumerates over cleartext LDAP.
# (domain provision strips this option, so write it into smb.conf directly.)
sed -i '/^\[global\]/a\\tldap server require strong auth = no' /etc/samba/smb.conf

# NOTE: all samba-tool provisioning below runs *offline*, directly against the
# on-disk AD database — Samba does not need to be running yet. We start Samba
# exactly once, in the foreground as PID 1, only after provisioning completes.
# (Starting a daemon here and then re-exec'ing a second foreground Samba makes
# the container exit immediately, since the daemon still holds the ports.)

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
        --userou="OU=Finance,OU=Corp" \
        --given-name="${user}" --surname="Corp" 2>/dev/null || true
    samba-tool group addmembers "Finance-Users" "${user}"
done
samba-tool group addmembers "Finance-Managers" "amurphy"
samba-tool group addmembers "Payroll-Access" "clee"

echo "[*] Creating IT users..."
samba-tool user create "tallen" "T@ll3n_IT@dmin!" \
    --userou="OU=IT,OU=Corp" 2>/dev/null || true
samba-tool group addmembers "Domain Admins" "tallen"
samba-tool group addmembers "IT-Admins" "tallen"

for user in sgarcia rrodriguez pmartinez qwalker ubrown vdavis; do
    samba-tool user create "${user}" "Welcome1!" \
        --userou="OU=IT,OU=Corp" 2>/dev/null || true
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
        --userou="OU=HR,OU=Corp" 2>/dev/null || true
    samba-tool group addmembers "HR-Users" "${user}"
done
samba-tool group addmembers "HR-Managers" "wevans"

echo "[*] Creating service accounts with SPNs (Kerberoastable)..."
samba-tool user create "svc-mssql" "Sql$3rv1ce2019!" \
    --userou="OU=ServiceAccounts" 2>/dev/null || true
samba-tool spn add "MSSQLSvc/db01.corp.local:1433" "svc-mssql"

samba-tool user create "svc-backup" "B@ckup$3rv1ce!" \
    --userou="OU=ServiceAccounts" 2>/dev/null || true
samba-tool spn add "BackupSvc/backup01.corp.local" "svc-backup"
samba-tool group addmembers "Backup Operators" "svc-backup" 2>/dev/null || true

samba-tool user create "svc-web" "W3b$3rv1ce2021!" \
    --userou="OU=ServiceAccounts" 2>/dev/null || true
samba-tool spn add "HTTP/intranet.corp.local" "svc-web"

echo "[*] Creating AS-REP roastable service accounts (no pre-auth)..."
samba-tool user create "svc-legacy" "L3g@cy$3rv1ce!" \
    --userou="OU=ServiceAccounts" 2>/dev/null || true
# Set DONT_REQUIRE_PREAUTH flag (userAccountControl 4194304)
samba-tool user setexpiry svc-legacy --noexpiry
python3 /data/set_nopreauth.py "svc-legacy" 2>/dev/null || \
    ldbmodify -H /var/lib/samba/private/sam.ldb /data/svc-legacy-nopreauth.ldif 2>/dev/null || true

samba-tool user create "svc-monitor" "M0n1t0r$3rv1ce!" \
    --userou="OU=ServiceAccounts" 2>/dev/null || true

echo "[*] Creating svc-deploy (member of IT-Admins — GenericWrite misconfiguration)..."
samba-tool user create "svc-deploy" "D3pl0y$3rv1ce!" \
    --userou="OU=ServiceAccounts" 2>/dev/null || true
samba-tool group addmembers "IT-Admins" "svc-deploy"

echo "[*] Domain provisioning complete."
echo "    Domain:      ${REALM}"
echo "    Admin:       Administrator / ${ADMIN_PASS}"
echo "    Test user:   jsmith / Welcome1!"
echo "    LDAP port:   389"
echo "    Kerberos:    88"

echo "[*] Starting Samba in the foreground..."
# Start Samba as PID 1 and keep the container alive.
exec samba --foreground --no-process-group
