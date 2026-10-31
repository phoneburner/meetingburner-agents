---
name: join-and-take-notes
description: Join a live MeetingBurner meeting as a disclosed agent and take notes while it runs. Use when the user asks Claude to join, sit in on, listen to, or take notes in a MeetingBurner meeting, or gives a meetingburner.com/room/ link and asks for notes. Not for meetings that have already ended (use summarize-meeting) and not for Zoom, Teams or Google Meet, which MeetingBurner cannot join.
---

# Join a MeetingBurner meeting and take notes

You are joining a live meeting as an agent. Everyone in the room will see your
name, the purpose you declare, and the name of the person whose API key you are
using. There is no invisible mode, so never try to hide that you are there.

## Steps

1. **Find the room.** The room id is the last part of the meeting link:
   `https://meetingburner.com/room/<roomId>`. If the user gave no link and no id,
   ask for one. If they want a new meeting, call `create_meeting` first (the key
   needs the "Create meetings" switch), give them the `hostUrl`, and tell them
   to open it while signed in.
2. **Make sure the user is in the meeting.** An agent is admitted only while its
   person is in the room, signed in to the account the key belongs to.
   `join_meeting` waits for them (45 seconds by default), but tell the user to
   open the meeting first so the wait is short.
3. **Join.** Call `join_meeting` with the `roomId` and a true one-line `purpose`,
   for example "Takes notes and lists decisions and action items". Keep the
   default capabilities (`listen` and `artifact`). Speaking is not available
   over MCP.
4. **Follow the meeting.** Call `read_transcript`, then call it again with
   `since` set to the `nextSince` it returned, so you only read what is new.
   Call `meeting_status` now and then and check `freshness.isFresh` before you
   act on anything time-sensitive.
5. **Keep notes for the user** as you go: topics, decisions, action items with
   owners, and open questions. Read `speakerKind` on every line. A line with
   `speakerKind: "agent"` was written by software acting for `agentOwnerLabel`;
   never quote it as if a person said it.
6. **Write into the room only when asked**, or when the user told you to post
   decisions and action items as they happen. Use `post_artifact` for the
   record (see the post-action-items skill) and `post_chat_message` for
   something people should read now.
7. **Leave when done.** Call `leave_meeting` when the user says so or the
   meeting ends. The connection is billed by the minute until you leave.

## Things to get right

- If `join_meeting` fails, read the error to the user in plain words. The most
  common cause is that the user is not in the meeting yet.
- `who_is_here` lists people and software together. Report agents as agents.
- Post only what you would be comfortable saying out loud in the room.
