#!/usr/bin/env python3
"""Minimal REST client for a Gluesync Core Hub.

Its whole job is to hold the credentials and report exactly what a call answered: a Core Hub error
carries the reason in its body, and losing that body turns a five-minute fix into an hour of guessing.

Configure through the environment (see gs_common.py): GLUESYNC_BASE, and either GLUESYNC_PAT or
GLUESYNC_USER + GLUESYNC_PASSWORD.

    python3 gs_api.py whoami                        # check URL and credentials
    python3 gs_api.py get /pipelines
    python3 gs_api.py post /pipelines '{"name": "demo"}'
    python3 gs_api.py put /pipelines/<id>/config/entities @entities.json   # body from a file
    python3 gs_api.py delete /connections/<id>

Nothing is cached on disk: a login token lives only for the duration of the process.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gs_common import parse, request  # noqa: E402

_TOKEN = None


def token():
    """A Personal API Token when one is set, otherwise a session token from /authentication/login."""
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    pat = os.environ.get("GLUESYNC_PAT")
    if pat:
        _TOKEN = pat
        return _TOKEN
    user, password = os.environ.get("GLUESYNC_USER"), os.environ.get("GLUESYNC_PASSWORD")
    if not (user and password):
        raise SystemExit("!! Set GLUESYNC_PAT, or GLUESYNC_USER and GLUESYNC_PASSWORD.")
    # The route is /authentication/login (not /login). Depending on the release the session token
    # comes back as `apiToken` or `token`, so accept either.
    _, _, text = request("POST", "/authentication/login", {"username": user, "password": password})
    answer = json.loads(text)
    _TOKEN = answer.get("apiToken") or answer.get("token")
    if not _TOKEN:
        raise SystemExit(f"!! login answered without a token: {list(answer)}")
    if answer.get("changeRequired"):
        print("  ! this account must change its password before other calls work "
              "(sign in to the Control Plane once, or POST /authentication/reset-password)", file=sys.stderr)
    return _TOKEN


def call(method, path, body=None, timeout=120):
    """Performs an authenticated call and returns the parsed body."""
    _, _, text = request(method, path, body, {"Authorization": "Bearer " + token()}, timeout)
    return parse(text)


def _body(arg):
    if arg is None:
        return None
    if arg.startswith("@"):
        with open(arg[1:]) as handle:
            return json.load(handle)
    return json.loads(arg)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    command = sys.argv[1].lower()
    if command == "whoami":
        version = call("GET", "/version")
        pipelines = call("GET", "/pipelines") or []
        print(json.dumps({"version": version, "pipelines": len(pipelines)}, indent=1))
        return 0
    if command in ("get", "post", "put", "patch", "delete") and len(sys.argv) >= 3:
        body = _body(sys.argv[3]) if len(sys.argv) > 3 else None
        print(json.dumps(call(command.upper(), sys.argv[2], body), indent=1))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
