#!/bin/bash
# Generate a self-signed certificate for the nginx demo
set -e

mkdir -p /etc/nginx/certs

openssl req -x509 -nodes -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -keyout /etc/nginx/certs/server.key \
  -out /etc/nginx/certs/server.crt \
  -days 365 \
  -subj "/CN=corp-fictional.com/O=Example Corp/C=US" \
  -addext "subjectAltName=DNS:nginx,DNS:nginx-weak,DNS:nginx-strong,DNS:localhost" \
  2>/dev/null

echo "Certificate generated at /etc/nginx/certs/"
openssl x509 -in /etc/nginx/certs/server.crt -noout -subject -dates
