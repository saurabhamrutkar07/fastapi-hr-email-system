#!/usr/bin/env bash
# Deploy the latest main branch on the EC2 server.
#
# Run as the ubuntu user. Called by:
#   - GitHub Actions (.github/workflows/deploy.yml) through AWS SSM, after CI passes on main
#   - the boot service (deploy/coldreach-deploy.service), so a server that was
#     off during a merge catches up as soon as it starts
#
# If the new version does not pass the health check, it rolls back to the
# last version that did (saved in LAST_GOOD_FILE) and still exits 1, so
# the failed deploy shows red in GitHub Actions. Database migrations are
# not rolled back: keep them backward compatible (add first, remove later).
#
# Everything is inside main() and the last line is "main; exit":
# bash reads a script while running it, and "git pull" may replace this
# very file. Reading the whole function first makes that safe.

set -euo pipefail

APP_DIR="/home/ubuntu/coldreach"
DOMAIN="saurabhamrutkar.com"
# Commit of the last deploy that passed the health check 
LAST_GOOD_FILE="/home/ubuntu/.coldreach-last-good"

# Build, restart and wait for api/health. Returns 1 if it never answers.
build_and_check() {
    echo "== Build and restart changed containers"
    # COMPOSE_FILE in .env adds docker-compose.prod.yml (HTTPS)
    docker compose up -d --build --remove-orphans || return 1 

    echo "== Wait for the app to answer"
    # Ask Nginx on this machine directly, with the real domain name for TLS
    for _ in $(seq 1 30); do 
        if curl -sf --resolve "${DOMAIN}:443:127.0.0.1" "https://${DOMAIN}/api/health" > /dev/null; then 
            return 0 
        fi 
        sleep 3
    done 
    return 1 
}

main() {
    cd "$APP_DIR"

    echo "== Pull latest main"
    git pull --ff-only
    git log --oneline -1

    if build_and_check; then
        git rev-parse HEAD > "$LAST_GOOD_FILE"
        echo "== Remove old unused images (keeps the disk from filling up)"
        docker image prune -f > /dev/null
        echo "Deploy OK"
        return 0
    fi

    echo "New version did not become healthy in 90 seconds" >&2
    docker compose ps
    docker compose logs --tail 50 api

    if [ ! -s "$LAST_GOOD_FILE" ]; then
        echo "No last good version saved, cannot roll back" >&2
        return 1
    fi

    LAST_GOOD=$(cat "$LAST_GOOD_FILE")
    echo "== Roll back to last good version ${LAST_GOOD:0:7}"
    git reset --hard "$LAST_GOOD"
    if build_and_check; then
        echo "Rolled back: the site runs the last good version. The deploy still FAILED." >&2
    else
        echo "Rollback also failed: the site is down, check it now" >&2
    fi
    # Always fail, so GitHub Actions shows a red deploy
    return 1
}
main; exit
