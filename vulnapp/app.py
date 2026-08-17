"""
Intentionally vulnerable local app — 팀원1's orchestration-flow test target.

Distinct from dast-harness/targets/vulnerable_app: this one exists to exercise
the *routing* (recon -> injection-agent / access-control-agent) across a wider
set of bug classes (SQLi, IDOR, unrestricted upload, missing auth, SSRF), not
to be a scored ground-truth target. Runs on 127.0.0.1:5000 only — do not
change the bind host or port mapping.

Do not deploy. Toy bearer-token auth, not production-grade.
"""
import os
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

USERS = {
    "alice-token": {"id": 1, "username": "alice", "role": "user"},
    "bob-token": {"id": 2, "username": "bob", "role": "user"},
    "admin-token": {"id": 3, "username": "admin", "role": "admin"},
}

# Simulated records table for the /search endpoint (kept in Python, not a
# real DB — the injection surface is the naive string-building below, which
# is what an injection-agent is meant to notice and exploit).
RECORDS = [
    {"id": 1, "title": "Q1 report", "owner": "alice", "note": "internal only"},
    {"id": 2, "title": "Q2 report", "owner": "bob", "note": "internal only"},
    {"id": 3, "title": "salary.csv", "owner": "admin", "note": "confidential"},
]

PROFILES = {
    1: {"id": 1, "username": "alice", "email": "alice@example.com", "ssn_last4": "1234"},
    2: {"id": 2, "username": "bob", "email": "bob@example.com", "ssn_last4": "5678"},
    3: {"id": 3, "username": "admin", "email": "admin@example.com", "ssn_last4": "0000"},
}


def current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return USERS.get(token)


@app.get("/search")
def search():
    # VULNERABLE: SQLi-style — naive string-building "query" over RECORDS.
    # Odd number of quotes => simulated syntax error (500). A trailing
    # "--" after breaking out of the quoted context => simulated recovery
    # that returns everything (classic error-based / comment-bypass shape).
    q = request.args.get("q", "")
    if q.count("'") % 2 == 1 and "--" not in q:
        return jsonify({"error": "SQL syntax error near '" + q + "'"}), 500
    if "' OR '1'='1" in q or "--" in q:
        return jsonify({"results": RECORDS})
    matches = [r for r in RECORDS if q.lower() in r["title"].lower()]
    return jsonify({"results": matches})


@app.get("/lookup")
def lookup():
    # Negative control — looks like /search but is NOT vulnerable. Long
    # input 500s with a generic error, never a SQL-flavored message.
    q = request.args.get("q", "")
    if len(q) > 100:
        return jsonify({"error": "input too long"}), 500
    matches = [r for r in RECORDS if q.lower() in r["title"].lower()]
    return jsonify({"results": matches})


@app.get("/user")
def get_user():
    # VULNERABLE: IDOR — ?id= is trusted with no ownership check beyond
    # "is someone logged in".
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    try:
        target_id = int(request.args.get("id", ""))
    except ValueError:
        return jsonify({"error": "bad id"}), 400
    profile = PROFILES.get(target_id)
    if not profile:
        return jsonify({"error": "not found"}), 404
    return jsonify(profile)


@app.get("/admin")
def admin():
    # VULNERABLE: missing auth entirely — no token check at all.
    return jsonify({
        "panel": "admin",
        "users": list(PROFILES.values()),
        "note": "this endpoint has no authentication check",
    })


@app.post("/upload")
def upload():
    # VULNERABLE: unrestricted file upload — no extension allowlist, no
    # content-type check, filename taken from the client mostly as-is
    # (only a minimal traversal guard so the demo can't escape vulnapp/).
    if "file" not in request.files:
        return jsonify({"error": "no file field"}), 400
    f = request.files["file"]
    filename = os.path.basename(f.filename or "upload.bin")
    dest = os.path.join(UPLOAD_DIR, filename)
    f.save(dest)
    return jsonify({"status": "saved", "path": f"/uploads/{filename}"})


@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    dest = os.path.join(UPLOAD_DIR, os.path.basename(filename))
    if not os.path.exists(dest):
        return jsonify({"error": "not found"}), 404
    with open(dest, "rb") as fh:
        return Response(fh.read(), mimetype="application/octet-stream")


@app.get("/fetch")
def fetch():
    # VULNERABLE: SSRF — server-side fetch of an arbitrary client-supplied
    # URL with no host allowlist. For exercises, keep the target URL on
    # loopback (e.g. url=http://127.0.0.1:5000/admin) to demonstrate
    # internal-pivot impact without making real external requests.
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            body = resp.read(2048)
            return jsonify({"status": resp.status, "body_excerpt": body.decode("utf-8", "replace")})
    except (urllib.error.URLError, ValueError) as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
