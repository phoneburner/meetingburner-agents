# MeetingBurner for AI coding agents

[MeetingBurner](https://meetingburner.com) is a video meeting service where AI
agents join as labelled participants: they listen, take notes and post
decisions and action items, and everyone in the room can see who they are.

This repository holds what a coding agent needs to build on MeetingBurner: a
Claude Code plugin with skills, and two starter projects. Developer docs:
[meetingburner.com/developers](https://meetingburner.com/developers).

## Claude Code plugin

```bash
claude plugin marketplace add phoneburner/meetingburner-agents
claude plugin install meetingburner@meetingburner
```

Claude Code asks once for your MeetingBurner API key (meetingburner.com,
**Settings**, **Developer**, **Create API Key**; it starts with `mb_`) and keeps
it in the system keychain. The plugin runs the
[`meetingburner-mcp`](https://www.npmjs.com/package/meetingburner-mcp) server
and adds three skills: join a meeting and take notes, post action items, and
summarise a finished meeting.

The [`claude-code-plugin/`](./claude-code-plugin) folder also has a Cursor rule
and an `AGENTS.md` snippet for Codex, Copilot and other agents. Details:
[claude-code-plugin/README.md](./claude-code-plugin/README.md).

## Starter projects

| Starter | What it does |
| --- | --- |
| [`examples/nextjs-agent-starter`](./examples/nextjs-agent-starter) | A small Next.js app that creates a meeting and sends an agent into it. Deploys to Vercel in one click |
| [`examples/python-agent-starter`](./examples/python-agent-starter) | A note-taking agent in plain Python, standard library only. Reads the live transcript and posts action items |

Each starter has its own README, plus `AGENTS.md` and `CLAUDE.md` so a coding
agent working in it follows the API's rules.

## Good to know

- Agents are always shown as agents, with their purpose and the name of the
  person who added them. There is no invisible mode.
- An agent is admitted only while the owner of its API key is in the meeting.
- Agent connections are billed to your account by the minute. Rates:
  [meetingburner.com/api-docs#usage](https://meetingburner.com/api-docs#usage).

## Licence

MIT. See [LICENSE](./LICENSE). To report a security issue, see
[SECURITY.md](./SECURITY.md).
