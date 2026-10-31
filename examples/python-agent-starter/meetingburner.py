"""
A tiny MeetingBurner Bot API client over plain HTTP: the Python standard
library only, no packages to install.

Every function here is one documented endpoint
(https://meetingburner.com/api-docs). agent.py is the part worth reading;
this file is the plumbing it calls.
"""

import json
import os
import time
import urllib.error
import urllib.request
import uuid

BASE_URL = os.environ.get("MEETINGBURNER_API_URL", "https://meetingburner.com/api/v1").rstrip("/")

# The server closes every event stream at 785 seconds; read a little longer.
STREAM_READ_TIMEOUT_SECONDS = 830

# Stored events are replayed on resume, so they are the ones to dedupe and resume from.
STORED_EVENTS = {"transcript.segment", "artifact.posted", "artifact.decided"}


class MeetingBurnerError(Exception):
    """A refusal from the API, carrying the HTTP status and the server's own words."""

    def __init__(self, status, body):
        self.status = status
        self.body = body
        super().__init__(f"{status}: {body.get('error', body)}")


def api_key():
    key = os.environ.get("MEETINGBURNER_API_KEY", "").strip()
    if not key.startswith("mb_"):
        raise SystemExit(
            "Set MEETINGBURNER_API_KEY to a MeetingBurner key (it starts with mb_). "
            "Create one at meetingburner.com: Settings, Developer, Create API Key."
        )
    return key


def request(method, path, body=None, headers=None):
    """Send one JSON request. Returns (status, body). Raises MeetingBurnerError on 4xx/5xx."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE_URL + path, data=data, method=method)
    req.add_header("X-API-Key", api_key())
    req.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as err:
        raise MeetingBurnerError(err.code, _json_or_text(err.read())) from None


def create_meeting(name):
    """POST /meetings. The key needs the 'Create meetings' switch."""
    _, body = request("POST", "/meetings", {"name": name}, {"Idempotency-Key": str(uuid.uuid4())})
    return body


def join(room_id, bot_name, purpose, max_wait_seconds=300):
    """POST /bots/join, waiting for the key's owner to arrive (202 waiting_for_owner)."""
    payload = {
        "roomId": room_id,
        "botName": bot_name,
        "capabilities": ["listen", "artifact"],
        "purpose": purpose,
        "waitForOwner": True,
    }
    deadline = time.monotonic() + max_wait_seconds
    while True:
        status, body = request("POST", "/bots/join", payload)
        if status == 200:
            return body
        if time.monotonic() >= deadline:
            raise SystemExit("You did not join the meeting in time. Open it while signed in, then run this again.")
        wait = body.get("retryAfterSeconds", 15)
        print(f"Waiting for you to join the meeting (checking again in {wait}s)...")
        time.sleep(wait)


def post_artifact(connection_id, artifact_type, text, assignee=None):
    """POST /bots/post-artifact: a decision, action item or question, shown to everyone."""
    body = {"connectionId": connection_id, "artifactType": artifact_type, "text": text}
    if assignee:
        body["assignee"] = assignee
    return request("POST", "/bots/post-artifact", body)[1]


def leave(connection_id):
    """POST /bots/leave. Always call it: connections are billed by the minute."""
    return request("POST", "/bots/leave", {"connectionId": connection_id})[1]


def events(room_id, connection_id):
    """Yield every meeting event until the meeting ends, reconnecting when the server asks."""
    cursor = None
    seen = set()
    while True:
        closing = None
        for event_id, event in _read_stream(room_id, connection_id, cursor):
            if event.get("type") == "stream.closing":
                closing = event
                break
            if event.get("type") in STORED_EVENTS and event_id:
                cursor = event_id
                row = event_id.split("|", 1)[-1]
                if row in seen:
                    continue
                seen.add(row)
            yield event
        if closing is not None and not closing.get("reconnect"):
            return
        if closing is not None:
            cursor = closing.get("cursor") or cursor
        else:
            time.sleep(2)  # the socket dropped; resume from the last stored event


def _read_stream(room_id, connection_id, cursor):
    url = f"{BASE_URL}/meetings/{room_id}/stream?connectionId={connection_id}"
    req = urllib.request.Request(url, headers={"X-API-Key": api_key(), "Accept": "text/event-stream"})
    if cursor:
        req.add_header("Last-Event-ID", cursor)
    try:
        with urllib.request.urlopen(req, timeout=STREAM_READ_TIMEOUT_SECONDS) as res:
            yield from parse_sse(res)
    except urllib.error.HTTPError as err:
        if err.code in (400, 401, 403, 404):
            raise MeetingBurnerError(err.code, _json_or_text(err.read())) from None
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return


def parse_sse(lines):
    """Turn an SSE byte stream into (id, event) pairs. Frames end with a blank line."""
    event_id, data = None, None
    for raw in lines:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":
            if data is not None:
                yield event_id, json.loads(data)
            event_id, data = None, None
        elif line.startswith("id: "):
            event_id = line[4:]
        elif line.startswith("data: "):
            data = line[6:]


def _json_or_text(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": raw.decode("utf-8", "replace")}
