# Hardening status

Only what is true today. "Open" items are gaps, listed so they can be planned, not hidden.

| Control | Status | Detail |
|---------|--------|--------|
| Sender allow-list | **Done** 2026-10-25 | Chat id compared with `TELEGRAM_CHAT_ID`; empty variable denies everyone. Unit-tested, not yet seen with a real message |
| Secrets out of workflows | **Done** | Bot token and API key are n8n credentials; the only environment variable the workflows read is the chat id. Exports pass `tools/sanitize_n8n.py` and the repo passes `tools/scan.py` in CI |
| Failure alerts | **Done**, not yet fired | Error Alert is set on all five workflows |
| Retries on network calls | **Done** | Three tries, five seconds apart, on Telegram, Claude and HTTP nodes |
| Safe destructive action | **Done** | Delete needs exactly one match and at least three letters |
| Database writes | **Partial** | Written through a temporary file and a rename, so a crash cannot leave a torn file. Two runs overlapping can still overwrite each other's change. Fix: limit n8n to one production execution at a time, or move to a real database |
| Backups | **Partial** | One manual backup was taken before the October changes. No schedule, no restore test |
| Prompt injection | **Partial** | The model has no tools and can only return text; a reply that is not valid JSON falls back to a plain capture. Notes and message text are placed in prompts as plain text, so text inside a note could still steer the answer |
| What leaves the server | **Partial** | Each general-chat request sends four notes (profile, goals, projects, current context) to the Claude API. Fine for one owner; worth narrowing before anyone else uses it |
| n8n settings | **Open** | Secure cookie off, external Code-node modules allowed with `*`, environment access allowed. Needed today for the Code nodes; each can be narrowed |
| Editor exposure | **To check** | The reference compose file binds the editor to localhost; confirm the live host does the same |
| Spend limit | **To check** | No cap or alert on model spend has been verified |
| Update policy | **Open** | The reference compose pins n8n 2.26.6; there is no scheduled update or version log |
| Log retention | **Open** | Executions keep message content; pruning is not configured here |
| Timed reminders | **Not built** | Reminders are stored as tasks and appear in the morning brief |
