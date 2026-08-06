#!/usr/bin/env bash
# Regenerate data/eve.json from the real anchor PCAP by running Suricata (ET Open).
#
# The committed data/eve.json is a real-but-modest curated corpus (the STRRAT capture
# yields ~875 events). Run this to reproduce it from source, or point PCAP_URL at a
# busier capture for true hundreds-of-thousands volume. Requires Docker on the host
# (the lab container has Python, not Suricata) — so run this on the host: `make gen`.
#
# Provenance is recorded in PROVENANCE.md. The PCAP is FETCHED, never mirrored.
set -euo pipefail

PCAP_URL="${PCAP_URL:-https://www.malware-traffic-analysis.net/2024/07/30/2024-07-30-traffic-analysis-exercise.pcap.zip}"
PCAP_SHA256="${PCAP_SHA256:-420530cefb5f0001e12aacc554cef14f6273f1e2ec01008567a68f3471e0ed70}"
ZIP_PASSWORD="${ZIP_PASSWORD:-infected_20240730}"   # MTA scheme: infected_YYYYMMDD (post date)
SURICATA_IMAGE="${SURICATA_IMAGE:-jasonish/suricata:latest}"

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo ">> fetching PCAP (fetched, never mirrored)"
curl -fsSL --max-time 300 -o "$WORK/capture.pcap.zip" "$PCAP_URL"

echo ">> verifying checksum"
GOT="$(shasum -a 256 "$WORK/capture.pcap.zip" | awk '{print $1}')"
if [ "$GOT" != "$PCAP_SHA256" ]; then
  echo "!! checksum mismatch: expected $PCAP_SHA256, got $GOT" >&2
  exit 1
fi

echo ">> unzipping"
unzip -o -P "$ZIP_PASSWORD" "$WORK/capture.pcap.zip" -d "$WORK" >/dev/null
PCAP="$(ls "$WORK"/*.pcap | head -1)"

echo ">> running Suricata ($SURICATA_IMAGE) with ET Open rules"
mkdir -p "$WORK/out"
docker run --rm --user 0:0 --entrypoint /bin/sh \
  -v "$WORK":/data -w /data "$SURICATA_IMAGE" -c \
  "suricata-update --no-test -q >/data/out/update.log 2>&1; \
   suricata -r /data/$(basename "$PCAP") -l /data/out -k none >/data/out/run.log 2>&1"

if [ ! -s "$WORK/out/eve.json" ]; then
  echo "!! Suricata produced no eve.json — see $WORK/out/run.log" >&2
  exit 1
fi

cp "$WORK/out/eve.json" "$HERE/data/eve.json"
echo ">> wrote $HERE/data/eve.json ($(wc -l < "$HERE/data/eve.json" | tr -d ' ') events)"
