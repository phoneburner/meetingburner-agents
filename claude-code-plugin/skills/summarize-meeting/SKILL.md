---
name: summarize-meeting
description: Summarise a MeetingBurner meeting that has ended, using its written summary, decisions, action items and transcript. Use when the user asks what happened in a MeetingBurner meeting, wants a recap, minutes, follow-up email or list of action items from a past meeting, or asks about meetings the API key created. Not for a meeting still running (use join-and-take-notes).
---

# Summarise a MeetingBurner meeting

These reads need the API key's "Read past meetings" switch
(`meetings:read`). They work only for a meeting that has ended, that was not
private or off the record, and that the key's owner hosted or attended signed
in.

## Steps

1. **Find the meeting.** Use the room id from the link the user gives you
   (`https://meetingburner.com/room/<roomId>`). If they do not have one, call
   `list_my_meetings`. It lists only meetings this key created, so an empty list
   does not mean they have no meetings; ask for the link instead.
2. **Read the summary.** Call `get_meeting_summary` with the `roomId`. It returns
   the written summary, key decisions, action items with owners, open questions,
   and the artifacts posted during the meeting.
3. **Read the transcript when you need detail** or when `summary` is null (the
   meeting was too short or had no transcript). Call `get_meeting_transcript`
   and page with `offset` set to the `nextOffset` it returned, until
   `nextOffset` is null. Quote the `display` string, which keeps who was a
   person and who was an agent.
4. **Write the recap** in this order: one-paragraph summary, decisions, action
   items (owner and task), open questions. Say which items came from the
   written summary and which you took from the transcript.

## Things to get right

- If a read is refused, tell the user the reason in plain words:
  - "meeting in progress": the meeting has not ended. Offer to join it instead.
  - "not recorded": the meeting was private or off the record, so there is no
    transcript to read. Do not describe it as a silent meeting.
  - "scope missing": the key needs "Read past meetings" switched on in
    Settings, Developer.
  - "not found": no such meeting, or one the key's owner was not in.
- Never present an agent's words as a person's. Every transcript line carries
  `speakerKind`.
