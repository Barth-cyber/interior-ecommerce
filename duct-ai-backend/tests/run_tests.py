import sys
import os
import json

# Ensure project root is on sys.path so we can import app
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app


def run():
    client = app.test_client()
    ok = True

    # /api/chat
    payload = {"messages": [{"role": "user", "content": "Hello from automated test"}], "session_id": "test"}
    resp = client.post("/api/chat", json=payload)
    if resp.status_code != 200:
        print("FAIL: /api/chat returned status", resp.status_code)
        ok = False
    else:
        data = resp.get_json() or {}
        if "reply" not in data:
            print("FAIL: /api/chat missing 'reply' in response")
            ok = False
        else:
            print("/api/chat reply:", data.get("reply"))

    # /config
    resp2 = client.get("/config")
    if resp2.status_code != 200:
        print("FAIL: /config returned status", resp2.status_code)
        ok = False
    else:
        print("/config response:", resp2.get_json())

    if not ok:
        sys.exit(2)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    run()
