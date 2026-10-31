# MeetingBurner for coding agents

Everything a coding agent needs to use MeetingBurner, in one folder:

| File | For | What it does |
| --- | --- | --- |
| [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json) | Claude Code | The plugin manifest. Asks once for your API key and stores it in the system keychain |
| [`.mcp.json`](./.mcp.json) | Claude Code | Starts the MeetingBurner MCP server, pinned to `meetingburner-mcp@0.1.0` |
| [`skills/`](./skills) | Claude Code | Three skills: join a meeting and take notes, post action items, summarise a meeting |
| [`../.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) | Claude Code | A one-plugin marketplace at the repository root, so the plugin installs by name |
| [`cursor/meetingburner.mdc`](./cursor/meetingburner.mdc) | Cursor | A project rule. Copy it to `.cursor/rules/` in your project |
| [`AGENTS.snippet.md`](./AGENTS.snippet.md) | Codex, Copilot, any agent | A section to paste into your project's `AGENTS.md` or `CLAUDE.md` |

## Before you start

1. A MeetingBurner API key: meetingburner.com, **Settings**, **Developer**,
   **Create API Key**. It starts with `mb_` and is shown once. Tick
   **Create meetings** and **Read past meetings** if you want those features;
   both are off by default.
2. Node.js 22 or later, because the MCP server runs with `npx`.

## Install in Claude Code

```bash
claude plugin marketplace add phoneburner/meetingburner-agents
claude plugin install meetingburner@meetingburner
```

Claude Code asks for your API key when the plugin is enabled. To try it for one
session without installing, run `claude --plugin-dir ./claude-code-plugin` from a checkout of
[phoneburner/meetingburner-agents](https://github.com/phoneburner/meetingburner-agents).

Then join a meeting yourself in a browser, signed in to the account the key
belongs to, and ask:

> Join my MeetingBurner meeting abc123 and take notes on decisions.

The skills are also available as commands: `/meetingburner:join-and-take-notes`,
`/meetingburner:post-action-items` and `/meetingburner:summarize-meeting`.

## What the agent can and cannot do

- It joins as a **disclosed agent**: everyone sees its name, its purpose and
  your name. There is no invisible mode.
- It joins only while **you** are in the meeting.
- It can read the live transcript, post decisions and action items, post in the
  meeting chat, and read ended meetings back. It cannot speak over MCP.
- Agent minutes are billed to your account. Rates are at
  [meetingburner.com/api-docs#usage](https://meetingburner.com/api-docs#usage).
- MeetingBurner cannot join Zoom, Teams or Google Meet meetings.

## Versions

The MCP server is pinned to `meetingburner-mcp@0.1.0` in `.mcp.json`, the
Cursor rule, the snippet and both starters. A new release updates all of them
together.
