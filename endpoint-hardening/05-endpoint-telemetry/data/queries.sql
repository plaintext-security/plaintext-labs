-- Module 05 — Endpoint Telemetry & EDR
-- Security-focused osquery queries
-- ATT&CK technique mapping included in each comment

-- Query 1: Running processes with network connections (C2 beaconing — T1071)
-- Detects processes with outbound network connections that may indicate C2 communication.
SELECT
  p.pid,
  p.name,
  p.path,
  p.cmdline,
  s.remote_address,
  s.remote_port,
  s.state
FROM processes p
JOIN process_open_sockets s ON p.pid = s.pid
WHERE s.remote_address NOT IN ('', '0.0.0.0', '::', '127.0.0.1', '::1')
  AND s.remote_port != 0
ORDER BY p.name;

-- Query 2: Users with login shells (T1078 — Valid Accounts)
-- Finds user accounts with interactive shells — excessive accounts = attack surface.
SELECT
  username,
  uid,
  gid,
  description,
  directory,
  shell
FROM users
WHERE shell NOT LIKE '%false'
  AND shell NOT LIKE '%nologin'
  AND shell NOT LIKE '%sync'
ORDER BY uid;

-- Query 3: Cron jobs (T1053.003 — Scheduled Task/Job: Cron)
-- Lists all cron entries — common persistence mechanism. The osquery table is
-- `crontab` (it parses /etc/cron.d/, /etc/crontab, and user crontabs). This surfaces
-- the seeded Atomic Red Team T1053.003 artifact: a cron entry running a payload from /tmp.
SELECT
  command,
  path,
  minute,
  hour,
  day_of_month,
  month,
  day_of_week
FROM crontab
ORDER BY path;

-- Query 4: SUID/SGID binaries (T1548.001 — Abuse Elevation Control: SUID/SGID)
-- Finds binaries with the SUID bit set — potential privilege escalation vectors.
SELECT
  path,
  permissions,
  uid,
  gid,
  size
FROM file
WHERE (path LIKE '/usr/bin/%' OR path LIKE '/usr/sbin/%' OR path LIKE '/bin/%')
  AND permissions LIKE '%s%'
  AND uid = 0
ORDER BY path;

-- Query 5: Listening ports (T1049 — System Network Connections Discovery)
-- Shows services accepting inbound connections — unexpected ports = potential backdoor.
SELECT
  p.name,
  p.pid,
  p.cmdline,
  l.address,
  l.port,
  l.protocol
FROM listening_ports l
JOIN processes p ON l.pid = p.pid
WHERE l.address != '127.0.0.1'
  AND l.address != '::1'
ORDER BY l.port;
