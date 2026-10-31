# nextjs-agent-starter

A tiny Next.js app that creates a MeetingBurner meeting through the
[Bot API](https://meetingburner.com/api-docs) and sends an agent into it.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fphoneburner%2Fmeetingburner-agents%2Ftree%2Fmain%2Fexamples%2Fnextjs-agent-starter&project-name=meetingburner-agent-starter&env=MEETINGBURNER_API_KEY&envDescription=Your%20MeetingBurner%20API%20key%20(starts%20with%20mb_)%2C%20with%20%22Create%20meetings%22%20ticked&envLink=https%3A%2F%2Fmeetingburner.com%2Fapi-docs)

1. **Create a meeting.** The app calls `POST /meetings` and shows the host link.
2. **Join it yourself**, signed in to MeetingBurner. An agent is admitted only
   while the person whose key it uses is in the room.
3. **Send the agent in.** The app calls `POST /bots/join` (asking it to wait for
   you), and once in, the agent posts a note into the meeting's Intel panel.
4. **Remove the agent** with `POST /bots/leave`.

The API key stays on the server: the browser only talks to this app's routes
under `app/api/`.

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
