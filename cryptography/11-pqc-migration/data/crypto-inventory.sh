#!/bin/bash
# crypto-inventory.sh <host[:port]> — read what the service ACTUALLY negotiates
# from the live handshake (NOT from the config file). This prints the baseline
# crypto inventory the learner records: per client role, the TLS version,
# negotiated key-exchange group, cipher, and server cert key type.
#
# Run it from each client container (modern + legacy) via `make inventory`. The
# point is that the inventory comes from the wire, not from grepping nginx.conf.
set -u

HOST="${1:-server:443}"
ROLE="${ROLE:-modern}"

# Modern client offers the hybrid group too; legacy cannot.
if [ "$ROLE" = "modern" ]; then
  GROUPS_FLAG="-groups X25519MLKEM768:X25519:prime256v1"
else
  GROUPS_FLAG=""
fi

OUT=$(echo "Q" | openssl s_client -connect "$HOST" -tls1_3 $GROUPS_FLAG 2>&1)

VER=$(printf '%s\n'   "$OUT" | grep -iE "Protocol\s*:" | head -1 | sed -E 's/.*:\s*//' | tr -d '\r')
GROUP=$(printf '%s\n' "$OUT" | grep -i "Negotiated TLS1.3 group:" | head -1 | sed -E 's/.*group:[[:space:]]*//I' | tr -d '\r')
[ -z "$GROUP" ] && GROUP=$(printf '%s\n' "$OUT" | grep -i "Server Temp Key:" | head -1 | sed -E 's/.*Key:[[:space:]]*//I' | tr -d '\r')
CIPHER=$(printf '%s\n' "$OUT" | grep -iE "^\s*Cipher\s*:" | head -1 | sed -E 's/.*:\s*//' | tr -d '\r')

# Cert key type from the presented server certificate.
CERT=$(echo "Q" | openssl s_client -connect "$HOST" 2>/dev/null </dev/null \
       | openssl x509 -noout -text 2>/dev/null \
       | grep -iE "Public Key Algorithm|Public-Key:" | head -2 | tr '\n' ' ' | tr -s ' ')

# Classify the key exchange: classical ECDHE is quantum-EXPOSED; a hybrid
# X25519MLKEM768 is quantum-resistant (safe if either component holds).
case "$GROUP" in
  *MLKEM*) CLASS="quantum-RESISTANT (hybrid)";;
  *)       CLASS="quantum-EXPOSED (classical key exchange)";;
esac

echo "=== crypto inventory: $ROLE client -> $HOST ==="
echo "  TLS version          : ${VER:-?}"
echo "  Negotiated KX group  : ${GROUP:-?}"
echo "  Cipher               : ${CIPHER:-?}"
echo "  Server cert key type : ${CERT:-?}"
echo "  Classification       : $CLASS"
echo "  (read from the live handshake, not the config)"
