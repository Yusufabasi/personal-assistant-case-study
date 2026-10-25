// Runs INSIDE the n8n container (see link-credentials.sh).
// Finds the Telegram and Anthropic credentials you created, writes their ids into the workflow
// files, and imports them again. Credential secrets are never printed or copied anywhere.
const fs = require("fs");
const { execFileSync } = require("child_process");

const SRC = "/tmp/pa-workflows";
const OUT = "/tmp/pa-linked";
const LIST = "/tmp/pa-credential-list.json";

execFileSync("n8n", ["export:credentials", "--all", `--output=${LIST}`], { stdio: "ignore" });
const all = JSON.parse(fs.readFileSync(LIST, "utf8"));
fs.unlinkSync(LIST); // holds the credentials in encrypted form; not needed after this point

const telegram = all.find((c) => c.type === "telegramApi");
const anthropic = all.find((c) => c.type === "anthropicApi");
if (!telegram || !anthropic) {
  console.error(
    "Missing credential: create one 'Telegram API' and one 'Anthropic API' credential in the n8n editor first."
  );
  process.exit(1);
}

fs.mkdirSync(OUT, { recursive: true });
let linked = 0;
for (const file of fs.readdirSync(SRC)) {
  const workflow = JSON.parse(fs.readFileSync(`${SRC}/${file}`, "utf8"));
  for (const node of workflow.nodes) {
    const c = node.credentials;
    if (!c) continue;
    if (c.telegramApi) { c.telegramApi = { id: telegram.id, name: telegram.name }; linked++; }
    if (c.anthropicApi) { c.anthropicApi = { id: anthropic.id, name: anthropic.name }; linked++; }
  }
  fs.writeFileSync(`${OUT}/${file}`, JSON.stringify(workflow));
}
console.log(`Linked ${linked} nodes to "${telegram.name}" and "${anthropic.name}".`);
execFileSync("n8n", ["import:workflow", "--separate", `--input=${OUT}`], { stdio: "inherit" });
