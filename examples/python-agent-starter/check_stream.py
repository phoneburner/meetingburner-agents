"""
A runnable check of the event stream's failure handling, against a fake
MeetingBurner on this machine. Standard library only, no key needed:

    python check_stream.py

It cuts the stream the ways a real network does (mid-chunk, at a chunk
boundary, with a frame that is not JSON) and checks that the agent logs,
reconnects from the last stored event and, when the server sends a final
stream.closing, prints its message and exits 0 with no traceback. It also
checks that five dropped connections in a row end the agent cleanly.
"""

import http.server
import json
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))


def frame(event_id, event):
    return f"id: {event_id}\ndata: {json.dumps(event)}\n\n".encode()


def line(n):
    event = {"type": "transcript.segment", "isFinal": True, "speakerName": "Sam", "speakerKind": "human", "text": f"line {n}"}
    return frame(f"2026-10-31T00:00:0{n}Z|row-{n}", event)


# One entry per stream connection, in order: (frames to send, how to end).
CUT_THEN_CLOSE = [
    ([line(1)], "mid_chunk"),  # http.client.IncompleteRead
    ([line(1), line(2)], "chunk_boundary"),  # socket closed with no terminating chunk
    ([b"data: {not json\n\n"], "clean"),  # a malformed frame: ValueError
    ([line(2), line(3), frame("x|close", {"type": "stream.closing", "reconnect": False, "reason": "meeting_ended", "message": "The host ended the meeting"})], "clean"),
]
# Nothing stored arrives, so these are failures in a row (a stored row would reset the count).
ALWAYS_CUT = [([], "mid_chunk")] * 10


class FakeMeetingBurner(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    script = []
    resume_ids = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        reply = {"/api/v1/bots/join": {"status": "connected", "connectionId": "c1"}}.get(self.path, {"durationSeconds": 1, "tokenCost": 0})
        body = json.dumps(reply).encode()
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).resume_ids.append(self.headers.get("Last-Event-ID"))
        if not type(self).script:
            self.send_error(500, "the check ran out of scripted streams")
            return
        frames, ending = type(self).script.pop(0)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for data in frames:
            self.wfile.write(b"%x\r\n%s\r\n" % (len(data), data))
        if ending == "mid_chunk":
            self.wfile.write(b"100\r\npartial")
        elif ending == "clean":
            self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()
        self.close_connection = True


def run_agent(script):
    FakeMeetingBurner.script = list(script)
    FakeMeetingBurner.resume_ids = []
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeMeetingBurner)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = dict(os.environ, MEETINGBURNER_API_KEY="mb_check", MEETINGBURNER_API_URL=f"http://127.0.0.1:{server.server_port}/api/v1")
    # Backoff sleeps are real, so shrink them: the check is about what is caught, not how long it waits.
    code = "import time, sys; time.sleep = lambda s: None; sys.argv = ['agent.py', 'join', 'room1']; import runpy; runpy.run_path('agent.py', run_name='__main__')"
    result = subprocess.run([sys.executable, "-c", code], cwd=HERE, env=env, capture_output=True, text=True, timeout=60)
    server.shutdown()
    return result, FakeMeetingBurner.resume_ids


def check(name, ok, result):
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    if not ok:
        print(f"  exit {result.returncode}\n  stdout: {result.stdout}\n  stderr: {result.stderr}")
    return ok


def main():
    results = []
    result, resumed = run_agent(CUT_THEN_CLOSE)
    out = result.stdout
    results.append(check("cut streams and a bad frame reconnect, then stream.closing exits 0", result.returncode == 0, result))
    results.append(check("no traceback", "Traceback" not in result.stderr, result))
    results.append(check("the closing message is printed", "The host ended the meeting" in out, result))
    results.append(check("each line is handed on once", [out.count(f"Sam: line {n}") for n in (1, 2, 3)] == [1, 1, 1], result))
    results.append(check("each reconnect resumes from the last stored event", resumed == [None, "2026-10-31T00:00:01Z|row-1", "2026-10-31T00:00:02Z|row-2", "2026-10-31T00:00:02Z|row-2"], result))
    results.append(check("the mid-chunk cut and the bad frame are logged by name", "IncompleteRead" in result.stderr and "JSONDecodeError" in result.stderr, result))

    result, resumed = run_agent(ALWAYS_CUT)
    results.append(check("five drops in a row: gives up with a plain message, exit 1", result.returncode == 1 and "failed 5 times in a row" in result.stderr, result))
    results.append(check("five drops in a row: no traceback, and it still leaves", "Traceback" not in result.stderr and "Left after" in result.stdout, result))
    results.append(check("five drops in a row: exactly five connections", len(resumed) == 5, result))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
