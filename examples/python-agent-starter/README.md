# python-agent-starter

A MeetingBurner meeting agent in plain Python. No packages to install: it uses
only the standard library and the public
[Bot API](https://meetingburner.com/api-docs).

It joins a live meeting as a **disclosed** note taker, prints who is there and
what they say, posts an action item into the meeting whenever a person says
"action item: ...", and leaves cleanly on Ctrl-C.

## Run it

You need Python 3.9 or later and a MeetingBurner API key (meetingburner.com,
**Settings**, **Developer**, **Create API Key**; tick **Create meetings** to use
`create`).

```bash
cp .env.example .env          # then put your key in .env
set -a; . ./.env; set +a      # load it into this shell

python agent.py create "Design review"
# open the hostUrl it prints, signed in, then:
python agent.py join <roomId>
```

The agent joins only while **you** are in the meeting. If you are not there
yet, it waits (up to five minutes) and joins when you arrive.

Say "Action item: send the deck to Sam" in the meeting and it appears in the
meeting's Intel panel, labelled as written by this agent on your behalf.

## Files

| File | What it is |
| --- | --- |
| `agent.py` | The agent. Change `on_line()` to call your own model |
| `meetingburner.py` | One function per API endpoint, plus the event stream with reconnects |
| `AGENTS.md`, `CLAUDE.md` | Notes for a coding agent working in this folder |

## Good to know

- Everyone in the meeting sees the agent's name, its purpose and your name.
  There is no invisible mode.
- Agent connections are billed to your account by the minute, so leave when
  done. Rates: [meetingburner.com/api-docs#usage](https://meetingburner.com/api-docs#usage).
- The event stream closes itself every 785 seconds. `meetingburner.events()`
  reconnects from the resume cursor, so a long meeting reads as one stream.
- MeetingBurner cannot join Zoom, Teams or Google Meet meetings.
