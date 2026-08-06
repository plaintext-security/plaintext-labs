#!/usr/bin/env bash
# Regenerate data/zeek/*.log by running Zeek over the SAME anchor PCAP that produced
# data/eve.json — so both sensors describe the identical STRRAT infection. Zeek emits
# native TSV logs (the `#fields`/`#types` header schema), a deliberately different shape
# from Suricata's EVE JSON: the "two sensors, one truth" contrast the M05 stretch uses.
#
# Requires Docker on the host (the lab container has Python, not Zeek). PCAP is fetched
# + checksum-verified, never mirrored. See data/PROVENANCE.md.
set -euo pipefail

PCAP_URL="${PCAP_URL:-https://www.malware-traffic-analysis.net/2024/07/30/2024-07-30-traffic-analysis-exercise.pcap.zip}"
PCAP_SHA256="${PCAP_SHA256:-420530cefb5f0001e12aacc554cef14f6273f1e2ec01008567a68f3471e0ed70}"
ZIP_PASSWORD="${ZIP_PASSWORD:-infected_20240730}"
ZEEK_IMAGE="${ZEEK_IMAGE:-zeek/zeek:latest}"
KEEP="${KEEP:-conn dns http ssl}"   # which logs to keep in data/zeek/

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

echo ">> fetching PCAP (fetched, never mirrored)"
curl -fsSL --max-time 300 -o "$WORK/cap.zip" "$PCAP_URL"
GOT="$(shasum -a 256 "$WORK/cap.zip" | awk '{print $1}')"
[ "$GOT" = "$PCAP_SHA256" ] || { echo "!! checksum mismatch: got $GOT" >&2; exit 1; }
unzip -o -P "$ZIP_PASSWORD" "$WORK/cap.zip" -d "$WORK" >/dev/null
PCAP="$(ls "$WORK"/*.pcap | head -1)"

echo ">> running Zeek ($ZEEK_IMAGE) over the pcap"
mkdir -p "$WORK/out"
docker run --rm --user 0:0 -v "$WORK":/data -w /data/out "$ZEEK_IMAGE" \
  zeek -C -r "/data/$(basename "$PCAP")"

mkdir -p "$HERE/data/zeek"
for f in $KEEP; do
  [ -f "$WORK/out/$f.log" ] && cp "$WORK/out/$f.log" "$HERE/data/zeek/$f.log"
done
echo ">> wrote $HERE/data/zeek/{$(echo $KEEP | tr ' ' ',')}.log"
