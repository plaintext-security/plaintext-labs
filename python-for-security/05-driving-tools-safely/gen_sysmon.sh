#!/usr/bin/env bash
# Fetch a real Sysmon EVTX sample (endpoint telemetry) for the third-sensor stretch.
#
# Unlike eve.json / Zeek (both derived from the shared pcap), host logs for that exact
# capture don't exist publicly — so this is a SEPARATE real incident: Samir Bousseaden's
# EVTX-ATTACK-SAMPLES, a Sysmon EventID 3 (network-connection) sample. It's the host side
# of an intrusion: which *process* opened a connection to which IP — what the network
# sensors on the wire can't see.
#
# The sample is **GPL-licensed upstream, so it is FETCHED, never mirrored/committed**
# (*.evtx is gitignored). Parsing it needs `python-evtx` (pip install python-evtx).
# See data/PROVENANCE.md.
set -euo pipefail

EVTX_URL="${EVTX_URL:-https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Command%20and%20Control/DE_sysmon-3-rdp-tun.evtx}"
EVTX_SHA256="${EVTX_SHA256:-1d1eb55d1b7c785db26e19b0d50b9eb4a7928671e4edeb82ea5182cb834c874a}"

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/data/sysmon"
mkdir -p "$OUT"

echo ">> fetching Sysmon EVTX (fetched, never mirrored; GPL upstream)"
curl -fsSL --max-time 180 -o "$OUT/sysmon.evtx" "$EVTX_URL"

GOT="$(shasum -a 256 "$OUT/sysmon.evtx" | awk '{print $1}')"
if [ "$GOT" != "$EVTX_SHA256" ]; then
  echo "!! checksum mismatch: expected $EVTX_SHA256, got $GOT" >&2
  exit 1
fi
echo ">> wrote $OUT/sysmon.evtx ($(shasum -a 256 "$OUT/sysmon.evtx" | awk '{print $1}'))"
echo ">> parse it with python-evtx, e.g.:  python -c \"from Evtx.Evtx import Evtx; ...\""
