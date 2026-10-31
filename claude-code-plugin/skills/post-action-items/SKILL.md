---
name: post-action-items
description: Post decisions, action items and open questions into a live MeetingBurner meeting's record, where every participant sees them. Use when the user asks Claude to post, log, record or write up action items, decisions, follow-ups or next steps in a MeetingBurner meeting that is still running. Requires being joined to the meeting first (see join-and-take-notes).
---

# Post action items into a MeetingBurner meeting

Posts go into the meeting's Intel panel, live, labelled as written by an agent
and attributed to you and the person whose key you use. Every participant reads
them, so post only what the room actually said or agreed.

## Steps

1. **Be in the meeting.** If you have not joined, follow the
   join-and-take-notes skill first. `post_artifact` writes into the meeting your
   connection joined; it takes no room id.
2. **Read before you write.** Call `read_transcript` (with `since` set to your
   last `nextSince`) so each item rests on something said in the room. Ignore
   lines with `speakerKind: "agent"` as evidence of what a person agreed.
3. **Post one item per call** with `post_artifact`:
   - `type`: `action_item` for a task, `decision` for something agreed,
     `key_question` for an open question. `insight`, `risk_signal`,
     `topic_shift` and `buy_signal` are also accepted.
   - `text`: one plain sentence, up to 2000 characters, for example
     "Send the revised pricing sheet before Friday".
   - `assignee`: only for `action_item`, and only the participant's exact
     display name as `who_is_here` shows it. Leave it out if nobody took it.
   - `confidence`: lower it (for example 0.6) when the owner or deadline was
     implied rather than said.
4. **Tell the user what you posted**, as a short list, so they can correct it.

## Things to get right

- Do not post the same item twice. Keep a list of what you already posted.
- Do not invent owners or deadlines. Say "no owner named" instead.
- If the post is refused with a capability error, the connection was joined
  without `artifact`. Leave and join again with the default capabilities.
- After the meeting has ended, posting fails. Use the summarize-meeting skill
  to read the record instead.
