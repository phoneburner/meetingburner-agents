<!--
  Paste the section below into your project's AGENTS.md (or CLAUDE.md) so any
  coding agent working in the repo uses MeetingBurner correctly.
-->

## MeetingBurner (live meetings for agents)

This project uses MeetingBurner. Agents join its meetings as labelled
participants. Full docs: https://meetingburner.com/api-docs. Prefer these notes
over anything remembered from training data.

- **Auth.** `X-API-Key` header with the key in `MEETINGBURNER_API_KEY` (starts
  with `mb_`). Never commit or log it.
- **Base URL.** `https://meetingburner.com/api/v1`.
- **MCP.** `npx -y meetingburner-mcp@0.1.0` with `MEETINGBURNER_API_KEY` set.
  Keep the version pinned.
- **Create a meeting.** `POST /meetings` with `{ "name": "..." }` and a fresh
  `Idempotency-Key` header. Returns `roomId`, `joinUrl` and `hostUrl`. Needs
  the key's "Create meetings" switch.
- **Join as an agent.** `POST /bots/join` with `roomId`, `botName`,
  `capabilities` (`["listen", "artifact"]` for notes) and a true one-line
  `purpose`. The key's owner must be in the meeting; send
  `"waitForOwner": true` and poll on `202`. `410` means the meeting ended.
- **Follow it.** `GET /meetings/{roomId}/stream?connectionId=...` (server-sent
  events). Reconnect with the resume cursor when it closes.
- **Write into it.** `POST /bots/post-artifact` with `connectionId`,
  `artifactType` (`decision`, `action_item`, `key_question`, ...) and `text`.
- **Leave.** `POST /bots/leave` with `connectionId`. Billing is per minute.
- **Afterwards.** `GET /meetings/{roomId}/summary` and `/transcript` (needs
  "Read past meetings").
- **Disclosure.** Agents are always shown as agents, with their purpose and
  owner. Never present an agent's line as a person's: check `speakerKind`.
