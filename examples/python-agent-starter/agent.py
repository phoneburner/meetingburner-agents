"""
python-agent-starter: a meeting agent in plain Python.

    python agent.py create "Design review"   # make a meeting, print its links
    python agent.py join <roomId>            # join it, print the meeting, post notes

`join` joins as a disclosed note taker, prints who is here and what they say,
posts an action item whenever someone says "action item:", and leaves cleanly
on Ctrl-C. Replace on_line() with your own model call to make it smarter.
"""

import sys

import meetingburner as mb

BOT_NAME = "Python Starter"
PURPOSE = "Takes notes and posts action items (python-agent-starter)"
ACTION_MARKER = "action item:"


def main(argv):
    if len(argv) == 3 and argv[1] == "create":
        return create(argv[2])
    if len(argv) == 3 and argv[1] == "join":
        return attend(argv[2])
    print(__doc__)
    return 2


def create(name):
    meeting = mb.create_meeting(name)
    print(f"Meeting created: {meeting['name']}")
    print(f"  You (the host), signed in: {meeting['hostUrl']}")
    print(f"  Guests:                    {meeting['joinUrl']}")
    print(f"Then run: python agent.py join {meeting['roomId']}")
    return 0


def attend(room_id):
    joined = mb.join(room_id, BOT_NAME, PURPOSE)
    connection_id = joined["connectionId"]
    print(f"Joined {room_id} as {BOT_NAME}. Everyone in the room can see this agent. Ctrl-C to leave.")
    try:
        for event in mb.events(room_id, connection_id):
            on_event(connection_id, event)
    except KeyboardInterrupt:
        pass
    finally:
        left = mb.leave(connection_id)
        print(f"\nLeft after {left.get('durationSeconds')}s. Billed: {left.get('tokenCost')} token(s).")
    return 0


def on_event(connection_id, event):
    kind = event.get("type")
    if kind == "ready":
        people = event["snapshot"]["participants"] + event["snapshot"]["agents"]
        print("In the room:", ", ".join(label(p) for p in people) or "(nobody yet)")
    elif kind == "meeting.ended":
        print("Meeting ended.")
    elif kind == "transcript.segment" and event.get("isFinal"):
        on_line(connection_id, event)


def on_line(connection_id, segment):
    """One finished line of the transcript. Agents are never shown as people."""
    speaker = segment["speakerName"]
    if segment.get("speakerKind") == "agent":
        speaker = f"{speaker} [agent for {segment.get('agentOwnerLabel')}]"
    print(f"{speaker}: {segment['text']}")

    text = segment["text"]
    marker = text.lower().find(ACTION_MARKER)
    if segment.get("speakerKind") == "human" and marker != -1:
        task = text[marker + len(ACTION_MARKER):].strip()
        if task:
            mb.post_artifact(connection_id, "action_item", task)
            print(f"  -> posted action item: {task}")


def label(person):
    if person.get("kind") == "human":
        return person["displayName"]
    return f"{person['displayName']} [{person['kind']}, added by {person.get('ownerLabel')}]"


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except mb.MeetingBurnerError as err:
        sys.exit(f"MeetingBurner refused: {err}")
