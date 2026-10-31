# nextjs-agent-starter

A tiny Next.js app that creates a MeetingBurner meeting through the
[Bot API](https://meetingburner.com/api-docs) and sends an agent into it.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fphoneburner%2Fmeetingburner-agents%2Ftree%2Fmain%2Fexamples%2Fnextjs-agent-starter&project-name=meetingburner-agent-starter&env=MEETINGBURNER_API_KEY,STARTER_ACCESS_TOKEN&envDescription=MEETINGBURNER_API_KEY%3A%20your%20MeetingBurner%20API%20key%20(starts%20with%20mb_)%2C%20with%20%22Create%20meetings%22%20ticked.%20STARTER_ACCESS_TOKEN%3A%20a%20long%20random%20secret%20that%20callers%20of%20this%20app%20must%20give.&envLink=https%3A%2F%2Fmeetingburner.com%2Fapi-docs)

1. **Create a meeting.** The app calls `POST /meetings` and shows the host link.
2. **Join it yourself**, signed in to MeetingBurner. An agent is admitted only
   while the person whose key it uses is in the room.
3. **Send the agent in.** The app calls `POST /bots/join` (asking it to wait for
   you), and once in, the agent posts a note into the meeting's Intel panel.
4. **Remove the agent** with `POST /bots/leave`.

The API key stays on the server: the browser only talks to this app's routes
under `app/api/`.

## Lock it before you deploy

Every route acts with **your** MeetingBurner key, so anyone who could call a
deployed copy could create meetings and send agents billed to you. The routes
therefore refuse every caller unless:

- **`STARTER_ACCESS_TOKEN` is set** (the Deploy button asks for it) and the
  request carries the same value. The page asks for it once and keeps it for
  the browser tab. Use a long random value, for example the output of
  `openssl rand -hex 32`, and share it only with people allowed to spend your
  minutes; or
- the app runs under **`npm run dev`** on your own machine, where no token is
  needed.

A deployed copy without the token refuses everything (it fails closed).

## Run it locally

You need Node.js 18.18 or later and a MeetingBurner API key (meetingburner.com,
**Settings**, **Developer**, **Create API Key**, with **Create meetings** ticked).

```bash
cp .env.example .env.local    # then put your key in .env.local
npm install
npm run dev                   # http://localhost:3000
```

## Make it your agent

This agent joins, says hello and waits. A serverless function cannot stay in a
meeting for long, so a real agent that listens runs somewhere that can hold a
connection open:

- Read the live meeting with `GET /meetings/{roomId}/stream?connectionId=...`
  from a long-running worker. `examples/python-agent-starter` in this
  repository shows the reconnect loop.
- Or let Claude do it: the MeetingBurner MCP server
  (`npx -y meetingburner-mcp@0.1.0`) joins, reads the transcript and posts
  action items for a model.

## Files

| File | What it is |
| --- | --- |
| `lib/meetingburner.ts` | One function per API call, server side only |
| `lib/access.ts` | Who may call the routes: the access token check |
| `app/api/meetings/route.ts` | Creates a meeting |
| `app/api/agent/route.ts` | Sends the agent in and posts one note |
| `app/api/agent/leave/route.ts` | Takes the agent out |
| `app/page.tsx` | The three buttons |
| `AGENTS.md`, `CLAUDE.md` | Notes for a coding agent working in this folder |

## Good to know

- Everyone in the meeting sees the agent's name, its purpose and your name.
- Agent connections are billed to your account by the minute. Rates:
  [meetingburner.com/api-docs#usage](https://meetingburner.com/api-docs#usage).
- MeetingBurner cannot join Zoom, Teams or Google Meet meetings.
