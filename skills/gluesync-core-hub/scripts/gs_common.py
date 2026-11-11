"""Shared HTTP plumbing for gs_api.py and mcp.py.

Dependency-free (urllib only) so the scripts run on any machine with Python 3.8+.

Configuration comes only from the environment, never from command-line arguments, so secrets do not
end up in shell history or in the process list:

    GLUESYNC_BASE           Core Hub base URL, e.g. https://gluesync.example.com:1717 (required)
    GLUESYNC_PAT            Personal API Token (gsp_...). Required for MCP; also accepted by REST
    GLUESYNC_USER           username for REST login (only used when no token is available)
    GLUESYNC_PASSWORD       password for REST login (only used when no token is available)
    GLUESYNC_CA_FILE        PEM bundle to trust, for a Core Hub with a private or self-signed CA
    GLUESYNC_INSECURE_TLS   set to 1 to skip certificate checks (test installs only)
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request


def base_url():
    base = os.environ.get("GLUESYNC_BASE", "").rstrip("/")
    if not base:
        raise SystemExit(
            "!! GLUESYNC_BASE is not set. Export your Core Hub URL first, e.g.\n"
            "   export GLUESYNC_BASE=https://gluesync.example.com:1717"
        )
    return base


def ssl_context():
    if os.environ.get("GLUESYNC_INSECURE_TLS") == "1":
        print("  ! TLS certificate checks are OFF (GLUESYNC_INSECURE_TLS=1)", file=sys.stderr)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    ca_file = os.environ.get("GLUESYNC_CA_FILE")
    return ssl.create_default_context(cafile=ca_file) if ca_file else ssl.create_default_context()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Core Hub redirects unknown paths to the UI. Surface that as an error instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, path, body=None, headers=None, timeout=120):
    """Performs one call. Returns (status, headers, text). Exits with the server's message on failure.

    The body of a failed Core Hub call usually says exactly what was wrong with the request, so it is
    always printed rather than swallowed.
    """
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base_url() + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    opener = urllib.request.build_opener(
        NoRedirect(), urllib.request.HTTPSHandler(context=ssl_context())
    )
    try:
        with opener.open(req, timeout=timeout) as response:
            return response.status, response.headers, response.read().decode()
    except urllib.error.HTTPError as error:
        if error.code in (301, 302, 303, 307, 308):
            raise SystemExit(
                f"!! {method} {path} -> {error.code} redirect to {error.headers.get('Location')}: "
                "unknown API path (Core Hub sends unknown paths to the UI). Check the path."
            )
        raise SystemExit(f"!! {method} {path} -> {error.code}: {error.read().decode()[:800]}")
    except urllib.error.URLError as error:
        raise SystemExit(
            f"!! {method} {path} -> not reachable: {error.reason}. "
            "Check GLUESYNC_BASE, that Core Hub is running, and TLS settings."
        )


def parse(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
