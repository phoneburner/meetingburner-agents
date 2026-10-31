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
import urllib.parse
import urllib.request
import uuid

BASE_URL = os.environ.get("MEETINGBURNER_API_URL", "https://meetingburner.com/api/v1").rstrip("/")

# Plain http is allowed only to this machine, for a local MeetingBurner.
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

# How many times one call waits out a 429 before giving up, and the longest wait.
MAX_RATE_LIMIT_RETRIES = 4
MAX_RETRY_AFTER_SECONDS = 60

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


def api_url(path):
    """
    The full URL for an API path, refused unless it is https (or http to this
    machine) on the configured MeetingBurner host. urllib also opens file://
    and other schemes, so nothing is opened that has not passed this check.
    """
    base = urllib.parse.urlsplit(BASE_URL)
    url = BASE_URL + path
    target = urllib.parse.urlsplit(url)
    secure = base.scheme == "https" or (base.scheme == "http" and base.hostname in LOOPBACK_HOSTS)
    if not secure or not base.hostname:
        raise SystemExit(f"MEETINGBURNER_API_URL must be an https:// URL (http only for localhost), not {BASE_URL!r}.")
    if (target.scheme, target.netloc) != (base.scheme, base.netloc) or not target.path.startswith(base.path + "/"):
        raise SystemExit(f"Refusing to call {url!r}: it is not under {BASE_URL!r}.")
    return url


def segment(value):
    """One path segment from an outside value (a room id, a connection id), escaped."""
    return urllib.parse.quote(str(value), safe="")


def request(method, path, body=None, headers=None):
    """
    Send one JSON request. Returns (status, body). Waits out a 429 using the
    server's Retry-After, a few times. Raises MeetingBurnerError on any other
    4xx/5xx, or on a 429 that does not clear.
    """
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        req = urllib.request.Request(api_url(path), data=data, method=method)
        req.add_header("X-API-Key", api_key())
        req.add_header("Content-Type", "application/json")
        for name, value in (headers or {}).items():
            req.add_header(name, value)
        try:
            with urllib.request.urlopen(req, timeout=30) as res:  # noqa: S310 - URL checked by api_url()
                return res.status, json.loads(res.read() or b"{}")
        except urllib.error.HTTPError as err:
            body_read = _json_or_text(err.read())
            if err.code != 429 or attempt == MAX_RATE_LIMIT_RETRIES:
                raise MeetingBurnerError(err.code, body_read) from None
            wait = retry_after_seconds(err.headers, body_read)
            print(f"MeetingBurner rate limit: waiting {wait}s before trying again...")
            time.sleep(wait)


def retry_after_seconds(headers, body=None):
    """The server's Retry-After (seconds) or retryAfterMs, bounded; 15s if it gave neither."""
    try:
        seconds = float(headers.get("Retry-After"))
    except (TypeError, ValueError):
        millis = (body or {}).get("retryAfterMs") if isinstance(body, dict) else None
        seconds = millis / 1000 if isinstance(millis, (int, float)) else 15
    return max(1, min(seconds, MAX_RETRY_AFTER_SECONDS))


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
    failures = 0
    while True:
        closing = None
        for event_id, event in _read_stream(room_id, connection_id, cursor):
            if event.get("type") == "stream.closing":
                closing = event
                break
            if event.get("type") in STORED_EVENTS and event_id:
                failures = 0  # a stored row arrived, so the stream is healthy again
                cursor = event_id
                row = event_id.split("|", 1)[-1]
                if row in seen:
                    continue
                seen.add(row)
            yield event
        if closing is not None and not closing.get("reconnect"):
            return
        if closing is not None and closing.get("reason") != "replay_failed":
            cursor = closing.get("cursor") or cursor
            failures = 0
            continue
        if closing is not None:
            cursor = closing.get("cursor") or cursor
        # A dropped socket, a busy server or a failed replay: back off, growing
        # only over failures in a row, then resume from the last stored event.
        failures += 1
        time.sleep(min(2 ** (failures - 1), 30))


def _read_stream(room_id, connection_id, cursor):
    path = f"/meetings/{segment(room_id)}/stream?connectionId={segment(connection_id)}"
    req = urllib.request.Request(api_url(path), headers={"X-API-Key": api_key(), "Accept": "text/event-stream"})
    if cursor:
        req.add_header("Last-Event-ID", cursor)
    try:
        with urllib.request.urlopen(req, timeout=STREAM_READ_TIMEOUT_SECONDS) as res:  # noqa: S310 - URL checked by api_url()
            yield from parse_sse(res)
    except urllib.error.HTTPError as err:
        body = _json_or_text(err.read())
        if err.code in (400, 401, 403, 404):
            raise MeetingBurnerError(err.code, body) from None
        if err.code == 429:
            wait = retry_after_seconds(err.headers, body)
            print(f"MeetingBurner rate limit on the event stream: waiting {wait}s...")
            time.sleep(wait)
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
