-- Module 12 — osquery cross-check for drift (the "observed state" view that
-- corroborates the Ansible --check diff). Run with:
--   osqueryi --json < data/drift-queries.sql
-- osquery is OPTIONAL in this lab (the Ansible --check/--diff loop is the
-- authoritative detector); these are the scheduled-pack queries you would
-- register in osquery.conf to watch the same three controls from the host side.

-- CIS-5.2.10 — root SSH login. Drift => a line containing 'PermitRootLogin yes'.
SELECT 'CIS-5.2.10' AS control, line
  FROM file_lines
 WHERE path = '/etc/ssh/sshd_config'
   AND line LIKE '%PermitRootLogin%';

-- CIS-3.3.7 — reverse-path filtering. Drift => current_value = '0'.
SELECT 'CIS-3.3.7' AS control, name, current_value
  FROM system_controls
 WHERE name = 'net.ipv4.conf.all.rp_filter';

-- CIS-6.1.10 — world-writable files under /srv/meridian. Any row == drift.
SELECT 'CIS-6.1.10' AS control, path, mode
  FROM file
 WHERE directory = '/srv/meridian'
   AND (mode LIKE '%6' OR mode LIKE '%7' OR mode LIKE '%2' OR mode LIKE '%3');
