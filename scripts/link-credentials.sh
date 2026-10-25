#!/usr/bin/env bash
# Attach your Telegram and Anthropic credentials to every node that needs them, then re-import.
# Run after creating the two credentials in the n8n editor. Safe to run again.
set -euo pipefail
cd "$(dirname "$0")/.."

C="${N8N_CONTAINER:-n8n}"

docker exec "$C" rm -rf /tmp/pa-workflows /tmp/pa-linked
docker cp workflows "$C:/tmp/pa-workflows"
docker cp scripts/link-credentials.js "$C:/tmp/link-credentials.js"
docker exec "$C" node /tmp/link-credentials.js

echo
echo "Linked. Importing switches workflows off, so open each of the 6 workflows and switch it on again."
