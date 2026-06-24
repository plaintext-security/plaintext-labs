#!/bin/bash
# Generate certificates for the three nginx TLS configurations
set -e

mkdir -p /etc/nginx/certs

# Generate a self-signed certificate for all three servers
openssl req -x509 -nodes -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -keyout /etc/nginx/certs/server.key \
  -out /etc/nginx/certs/server.crt \
  -days 365 \
  -subj "/CN=corp-fictional.com/O=Example Corp/C=US" \
  -addext "subjectAltName=DNS:nginx-legacy,DNS:nginx-modern,DNS:nginx-strong,DNS:localhost" \
  2>/dev/null

echo "Certificates generated."
