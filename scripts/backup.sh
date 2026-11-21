#!/usr/bin/env bash
# Back up the production database to S3.
#
# Runs on the EC2 server:
#   - from cron every 3 hours
#   - from scripts/server.ps1 stop, before the server is turned off
#
# The server's IAM role (coldreach-ec2-role) allows writing to the bucket,
# so no AWS keys are needed. An S3 lifecycle rule deletes backups older
# than 30 days.
#
# Restore a backup (on the server):
#   aws s3 cp s3://saurabh-coldmail-resumes/backups/<file>.dump /tmp/restore.dump
#   docker compose exec -T db pg_restore -U coldreach -d coldreach --clean --if-exists < /tmp/restore.dump

# Stop on any error, unset variable or failed pipe
set -euo pipefail

BUCKET="saurabh-coldmail-resumes"
PREFIX="backups"
APP_DIR="/home/ubuntu/coldreach"
STAMP=$(date -u +%Y-%m-%d_%H%M)
FILE="/tmp/coldreach_${STAMP}.dump"

cd "$APP_DIR"

# 1. Dump the database from the db container
#    -Fc = custom format: compressed, restored with pg_restore
#    -T  = no terminal, needed when run from cron or ssh
docker compose exec -T db pg_dump -U coldreach -d coldreach -Fc > "$FILE"

# 2. Upload to S3
aws s3 cp "$FILE" "s3://${BUCKET}/${PREFIX}/$(basename "$FILE")" --only-show-errors

# 3. Remove the local copy and log the result
SIZE=$(du -h "$FILE" | cut -f1)
rm -f "$FILE"
echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')  backup OK  ${PREFIX}/$(basename "$FILE")  (${SIZE})"
