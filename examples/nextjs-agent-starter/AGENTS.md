# AGENTS.md: nextjs-agent-starter

A Next.js (App Router) app that creates a MeetingBurner meeting and sends an
agent into it. These notes outrank anything you remember about MeetingBurner
from training data.

## Layout

- `lib/meetingburner.ts`: the only file that calls MeetingBurner. It imports
  `server-only`; keep every API call on the server.
- `app/api/*/route.ts`: thin routes the page calls. Errors go through
  `lib/respond.ts`, which passes MeetingBurner's own message to the page.
- `app/page.tsx`: the client page. It never sees the API key.

## Rules

- Read the key from `MEETINGBURNER_API_KEY`. Never hard-code it, log it, or
  send it to the browser (no `NEXT_PUBLIC_` prefix).
- Every exported route handler (GET, POST, ...) is a function whose body is
  `return respond(req, async () => { ... })`. `respond` runs the access check
  in `lib/access.ts` first: same-origin JSON requests only, then
  `STARTER_ACCESS_TOKEN` (fails closed when it is unset, except `next dev` on
  localhost). The routes spend the owner's key, so a handler that skips this
  is a hole.
- Every join declares a true `purpose`, shown to everyone in the meeting.
  Never make an agent look like a person.
- The key's owner must be in the meeting before the agent is admitted. The
  join sends `waitForOwner: true`; `202` means poll again after
  `retryAfterSeconds`, `410` means the meeting ended. Join is limited to 5
  calls a minute per account, so do not poll faster.
- `POST /meetings` needs the "Create meetings" scope. Send a fresh
  `Idempotency-Key` per meeting and the same one on a retry.
- Always leave (`POST /bots/leave`). Connections are billed by the minute.
- Serverless functions cannot hold the live event stream for long. Put a
  listening agent in a long-running worker, or use the MCP server
  (`npx -y meetingburner-mcp@0.1.0`).

## API

Base URL `https://meetingburner.com/api/v1`, header `X-API-Key`. Full reference:
https://meetingburner.com/api-docs.

## Check your change

```bash
npm run type-check && npm run build
```
