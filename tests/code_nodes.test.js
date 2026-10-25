// Runs the Code-node bodies from workflows/*.json against a throwaway SQLite database
// built from sql/schema.sql. No n8n, Telegram or Claude needed.
//
//   npm install sql.js && node tests/code_nodes.test.js
//
// SQLJS_PATH overrides where sql.js is loaded from (the n8n container keeps it at
// /home/node/.n8n/nodes/node_modules/sql.js).
const fs = require("fs");
const os = require("os");
const path = require("path");

const root = path.resolve(__dirname, "..");
const SQLJS = process.env.SQLJS_PATH || "sql.js";
const initSqlJs = require(SQLJS);
const TEST_DB = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "pa-test-")), "test.db");
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

const workflows = Object.fromEntries(
  fs.readdirSync(path.join(root, "workflows")).map((f) => {
    const wf = JSON.parse(fs.readFileSync(path.join(root, "workflows", f), "utf8"));
    return [wf.name, wf];
  })
);
const codeOf = (wfName, node) => workflows[wfName].nodes.find((n) => n.name === node).parameters.jsCode;

const results = [];
const check = (name, ok, detail = "") => {
  results.push(ok);
  console.log((ok ? "PASS " : "FAIL ") + name + (detail ? "  [" + detail + "]" : ""));
};

// n8n code nodes hard-code these two paths; point them at the test database and sql.js
async function run(code, { input = {}, env = {}, items = null, helpers = {} } = {}) {
  const body = code
    .split("/home/node/.n8n/assistant.db").join(TEST_DB)
    .split("/home/node/.n8n/nodes/node_modules/sql.js").join(SQLJS);
  const $input = { first: () => ({ json: input }), all: () => (items || [input]).map((json) => ({ json })) };
  const $ = () => ({ item: { json: {} } });
  return new AsyncFunction("$input", "$env", "$", "require", body).call({ helpers }, $input, env, $, require);
}
async function withDb(fn) {
  const SQL = await initSqlJs();
  const db = new SQL.Database(fs.readFileSync(TEST_DB));
  const out = fn(db);
  fs.writeFileSync(TEST_DB, Buffer.from(db.export()));
  db.close();
  return out;
}
const rows = (sql) => withDb((db) => (db.exec(sql)[0] || { values: [] }).values);
const exec = (...sqls) => withDb((db) => sqls.forEach((s) => db.run(s)));

(async () => {
  const SQL = await initSqlJs();
  const fresh = new SQL.Database();
  fresh.exec(fs.readFileSync(path.join(root, "sql", "schema.sql"), "utf8"));
  fs.writeFileSync(TEST_DB, Buffer.from(fresh.export()));
  fresh.close();

  const PA = "Personal Assistant v2";

  // Sender allow-list
  const parse = codeOf(PA, "ParseCommand");
  const msg = (chat) => ({ message: { text: "hello", chat: { id: chat }, message_id: 7 } });
  let r = await run(parse, { input: msg(111), env: { TELEGRAM_CHAT_ID: "111" } });
  check("allow-list: owner is let through", r.length === 1 && r[0].json.chat_id === "111");
  r = await run(parse, { input: msg(222), env: { TELEGRAM_CHAT_ID: "111" } });
  check("allow-list: stranger is dropped", r.length === 0);
  r = await run(parse, { input: msg(111), env: {} });
  check("allow-list: missing env var denies everyone", r.length === 0);

  // Reminders are stored, and the reply says so
  r = await run(codeOf(PA, "HandleReminder"), {
    input: { chat_id: "1", original_text: "call John", params: { text: "call John", remind_at: "2026-11-03T15:00" } },
  });
  const t = await rows("select due_date from tasks where context_tag='reminder'");
  check("reminder: stored as a task with its due date", t.length === 1 && t[0][0] === "2026-11-03");
  check("reminder: reply says it is a task, not a timed reminder", /Saved as a task/.test(r[0].json.message));

  // Delete only when exactly one task matches
  const del = codeOf(PA, "HandleDeleteTask");
  await exec("delete from tasks", "insert into tasks (title,status) values ('buy milk','pending'),('buy bread','pending'),('write report','pending')");
  r = await run(del, { input: { chat_id: "1", params: { filter: "bu" } } });
  check("delete: filter shorter than 3 letters is refused", /at least 3/.test(r[0].json.message));
  r = await run(del, { input: { chat_id: "1", params: { filter: "buy" } } });
  check("delete: two matches deletes nothing", /nothing deleted/.test(r[0].json.message) && (await rows("select count(*) from tasks"))[0][0] === 3);
  r = await run(del, { input: { chat_id: "1", params: { filter: "report" } } });
  check("delete: exactly one match is deleted", /Deleted task: write report/.test(r[0].json.message) && (await rows("select count(*) from tasks"))[0][0] === 2);
  check("delete: no .tmp file left behind", !fs.existsSync(TEST_DB + ".tmp"));

  // A handler that only gained the atomic write
  r = await run(codeOf(PA, "HandleExpense"), { input: { chat_id: "1", original_text: "lunch", params: { amount: 500, category: "food", description: "lunch" } } });
  check("atomic write: expense handler still works", /Logged/.test(r[0].json.message) && (await rows("select count(*) from expenses"))[0][0] === 1 && !fs.existsSync(TEST_DB + ".tmp"));

  // Morning Brief greeting (was calling a method that does not exist)
  r = await run(codeOf("Morning Brief v2", "GatherAllContext"), { env: { TELEGRAM_CHAT_ID: "111" } });
  check("morning brief: builds context and a greeting", /^Good (morning|afternoon|evening)$/.test(r[0].json.greeting), r[0].json.greeting);

  // Intel Brief: json must be an object, and both input shapes must work
  const hn = codeOf("Intel Brief Scanner", "FetchHNDetails");
  const helpers = { httpRequest: async ({ url }) => ({ id: Number(url.match(/item\/(\d+)/)[1]), title: "T", score: 5 }) };
  r = await run(hn, { items: [[101, 102, 103]], helpers });
  check("intel brief: id list arriving as one array item", r[0].json.items && r[0].json.items.length === 3);
  r = await run(hn, { items: [{ data: 201 }, { data: 202 }], helpers });
  check("intel brief: ids arriving one item per id", r[0].json.items && r[0].json.items.length === 2);
  r = await run(codeOf("Intel Brief Scanner", "ParseGitHub"), {
    input: { items: [{ full_name: "a/b", description: "d", html_url: "u", stargazers_count: 3, language: "Py", topics: [] }] },
  });
  check("intel brief: GitHub parse returns an object", r[0].json && !Array.isArray(r[0].json) && r[0].json.items.length === 1);

  const failed = results.filter((x) => !x).length;
  console.log(`\n${results.length - failed}/${results.length} passed`);
  process.exit(failed ? 1 : 0);
})().catch((e) => {
  console.error("HARNESS ERROR:", e);
  process.exit(2);
});
