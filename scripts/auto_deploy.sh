#!/bin/bash
# Newsbox Auto-Deploy Watcher Script
# Checks remote main branch every 60s and rebuilds if changes are found.

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR" || exit 1

echo "Starting Newsbox Auto-Deploy Watcher in $APP_DIR..."

while true; do
    git fetch origin main --quiet
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] New commit detected on origin/main. Deploying..."
        git pull origin main
        sudo docker compose up -d --build
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployment finished."
    fi

    sleep 60
done
