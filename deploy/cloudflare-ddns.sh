#!/usr/bin/env bash
# Point the domain's DNS A record at this server's current public IP.
#
# Why: an EC2 server gets a new public IP every time it starts.
# This script runs on every boot (deploy/cloudflare-ddns.service) and
# tells Cloudflare the new IP, so the domain keeps working.
#
# Settings come from /etc/coldreach/cloudflare.env (root only, chmod 600):
#   CF_API_TOKEN    Cloudflare token: DNS Edit on this one zone only
#   CF_ZONE_ID      the domain's Zone ID (Cloudflare overview page)
#   CF_RECORD_NAME  the A record to update, e.g. saurabhamrutkar.com
#
# Install on the server:
#   sudo install -m 755 deploy/cloudflare-ddns.sh /usr/local/bin/coldreach-ddns.sh

# Stop on any error, unset variable or failed pipe
set -euo pipefail

source /etc/coldreach/cloudflare.env

CF_API="https://api.cloudflare.com/client/v4"
AUTH="Authorization: Bearer $CF_API_TOKEN"
# At boot the network may need a few seconds, so retry
CURL="curl -sf --retry 10 --retry-delay 3 --retry-all-errors"

# 1. Ask EC2 for this server's public IP (IMDSv2: get a session token first)
IMDS="http://169.254.169.254/latest"
META_TOKEN=$($CURL -X PUT "$IMDS/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
NEW_IP=$($CURL -H "X-aws-ec2-metadata-token: $META_TOKEN" "$IMDS/meta-data/public-ipv4")

# 2. Find the A record in Cloudflare (we need its id and current IP)
RECORD=$($CURL -H "$AUTH" "$CF_API/zones/$CF_ZONE_ID/dns_records?type=A&name=$CF_RECORD_NAME")
RECORD_ID=$(echo "$RECORD" | python3 -c 'import sys, json; print(json.load(sys.stdin)["result"][0]["id"])')
OLD_IP=$(echo "$RECORD" | python3 -c 'import sys, json; print(json.load(sys.stdin)["result"][0]["content"])')

# 3. Nothing to do if Cloudflare already has this IP (e.g. a reboot)
if [ "$NEW_IP" = "$OLD_IP" ]; then
    echo "DNS already points to $NEW_IP, nothing to change"
    exit 0
fi

# 4. Change only the IP; name, TTL and proxy setting stay as they are
$CURL -X PATCH -H "$AUTH" -H "Content-Type: application/json" \
    "$CF_API/zones/$CF_ZONE_ID/dns_records/$RECORD_ID" \
    --data "{\"content\": \"$NEW_IP\"}" > /dev/null

echo "DNS updated: $CF_RECORD_NAME $OLD_IP -> $NEW_IP"
