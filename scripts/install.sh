#!/usr/bin/env bash
# Start n8n, install the SQLite library, create the assistant database, import the workflows.
# Needs only Docker. Safe to run again: it never overwrites an existing database.
set -euo pipefail
cd "$(dirname "$0")/.."

C="${N8N_CONTAINER:-n8n}"
URL="${N8N_URL:-http://127.0.0.1:5678}"

[ -f .env ] || { echo "Copy .env.example to .env and fill it in first."; exit 1; }
grep -q '^TELEGRAM_CHAT_ID=.\+' .env || { echo "Set TELEGRAM_CHAT_ID in .env first (the assistant ignores everyone else)."; exit 1; }

mkdir -p n8n-data
echo "1/4 Starting n8n..."
docker compose up -d
for _ in $(seq 1 90); do
  curl -fsS "$URL/healthz" >/dev/null 2>&1 && break
  sleep 2
done
curl -fsS "$URL/healthz" >/dev/null 2>&1 || { echo "n8n did not become ready. Check: docker logs $C"; exit 1; }

echo "2/4 Installing the SQLite library (sql.js)..."
docker exec "$C" sh -c 'mkdir -p /home/node/.n8n/nodes && cd /home/node/.n8n/nodes && { [ -d node_modules/sql.js ] || npm install --silent sql.js@1.14.1; }'

echo "3/4 Creating the assistant database..."
docker cp sql/schema.sql "$C:/tmp/pa-schema.sql"
docker exec "$C" node -e '
const fs = require("fs");
const init = require("/home/node/.n8n/nodes/node_modules/sql.js");
const path = "/home/node/.n8n/assistant.db";
if (fs.existsSync(path)) { console.log("   assistant.db already exists, left as it is"); process.exit(0); }
init().then((SQL) => {
  const db = new SQL.Database();
  db.exec(fs.readFileSync("/tmp/pa-schema.sql", "utf8"));
  fs.writeFileSync(path, Buffer.from(db.export()));
  console.log("   created assistant.db");
});'

echo "4/4 Importing the workflows..."
docker exec "$C" rm -rf /tmp/pa-workflows
docker cp workflows "$C:/tmp/pa-workflows"
docker exec "$C" n8n import:workflow --separate --input=/tmp/pa-workflows 2>&1 | grep -E "Successfully|rror" | grep -v "Error tracking" || true

cat <<EOF

Done. Three things left, all in the n8n editor at $URL

  1. Create the owner account, then add two credentials:
       - "Telegram API"    your bot token from @BotFather
       - "Anthropic API"   your API key from console.anthropic.com
  2. Run:  ./scripts/link-credentials.sh
  3. Open each of the 6 workflows and switch it on (the Active / Publish toggle).
     Switch on "Error Alert" last. Telegram needs WEBHOOK_URL in .env to be a public https address.

Then message your bot.
EOF
