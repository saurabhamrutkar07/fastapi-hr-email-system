#!/usr/bin/env bash
# Deploy the latest main branch on the EC2 server.
#
# Run as the ubuntu user. Called by:
#   - GitHub Actions (.github/workflows/deploy.yml) through AWS SSM, after CI passes on main
#   - the boot service (deploy/coldreach-deploy.service), so a server that was
#     off during a merge catches up as soon as it starts
#
# Everything is inside main() and the last line is "main; exit":
# bash reads a script while running it, and "git pull" may replace this
# very file. Reading the whole function first makes that safe.

set -euo pipefail

APP_DIR="/home/ubuntu/coldreach"
DOMAIN="saurabhamrutkar.com"

main() {
    cd "$APP_DIR"

    echo "== Pull latest main"
    git pull --ff-only
    git log --oneline -1

    echo "== Build and restart changed containers"
    # COMPOSE_FILE in .env adds docker-compose.prod.yml (HTTPS)
    docker compose up -d --build --remove-orphans

    echo "== Remove old unused images (keeps the disk from filling up)"
    docker image prune -f > /dev/null

    echo "== Wait for the app to answer"
    # Ask Nginx on this machine directly, with the real domain name for TLS
    for _ in $(seq 1 30); do
        if curl -sf --resolve "${DOMAIN}:443:127.0.0.1" "https://${DOMAIN}/api/health" > /dev/null; then
            echo "Deploy OK"
            return 0
        fi
        sleep 3
    done

    echo "App did not become healthy in 90 seconds" >&2
    docker compose ps
    docker compose logs --tail 50 api
    return 1

}
main; exit
