# How it grew

Every date below comes from a timestamp in the n8n database, the assistant's own database, or
the notes it keeps. Nothing is reconstructed from memory.

| Date | What happened | Evidence |
|------|---------------|----------|
| 2026-06-17 | n8n instance set up (owner account created) | n8n database |
| 2026-06-19 | First message stored. The project notes of that day record the Telegram capture flow as live, with the evening check-in as the next step | `messages` table; vault notes |
| Jun to Aug | A first router (MainRouter) captured messages into the notes and the database | build notes |
| 2026-08-26 | **Rebuild.** A written build plan (5 phases, 19 features, 14 new tables) was turned into workflow JSON by a 1,670-line generator script. The same day the new router went through 17 saved versions, and the evening, morning, weekly and intel workflows were created and revised | build plan; workflow version counters |
| 2026-08-29 | Last message stored (25 in total, 2026-06-19 to 2026-08-29) | `messages` table |
| 2026-10-11 | Earliest retained scheduled run. n8n keeps only recent history, so earlier runs are not visible | execution history |
| 2026-10-12 to 10-24 | Morning Brief and Intel Brief fail on every retained run; Evening Reflection fails on some | execution history |
| 2026-10-25 | **Audit and repair.** Cause of each failure found, fixes applied to the live instance, runs verified. See [the audit](audit-2026-10-25.md) | this repo |

## What the design looked like at each stage

**Capture (June).** Message in, note out. One workflow, no memory beyond the notes.

**Life tracker (August).** The build plan turned it into a classifier-and-handlers system: every
message is first classified into one of 15 intents, then a small handler writes to the right
table. Habits, mood, expenses, tasks, ideas and knowledge became first-class data, and the
scheduled workflows read that data back to write the morning brief, the evening prompt and the
weekly review.

**Reliable (October).** The system had been running unwatched. Two of its five workflows had
never succeeded on a schedule, and nothing told the owner. The October work added the missing
pieces: an alert when anything fails, retries on network calls, a sender allow-list, and
tests for the logic that moves money-adjacent and personal data.

## Planned but not built

The build plan also lists calendar integration, email digest and draft replies, a contact
follow-up engine and an accountability engine. The tables for some of these exist
(`emails`, `email_drafts`, `contacts`, `commitments`), but no workflow uses them yet.
