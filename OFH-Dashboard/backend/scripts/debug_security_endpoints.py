#!/usr/bin/env python3
"""Call security endpoints via Flask test client to inspect payloads."""

import os
from pathlib import Path
from pprint import pprint

from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv()

from app import app


def fetch_security_snapshots():
    with app.test_client() as client:
        print("=== /api/security/overview ===")
        resp = client.get("/api/security/overview")
        pprint(resp.json)

        print("\n=== /api/security/threats?timeRange=7d ===")
        resp = client.get("/api/security/threats", query_string={"timeRange": "7d"})
        pprint(resp.json)

        print("\n=== /api/security/access?timeRange=7d ===")
        resp = client.get("/api/security/access", query_string={"timeRange": "7d"})
        pprint(resp.json)

        print("\n=== /api/security/compliance?hours=720 ===")
        resp = client.get("/api/security/compliance", query_string={"hours": "720"})
        pprint(resp.json)

        print("\n=== /api/security/incidents?timeRange=7d ===")
        resp = client.get(
            "/api/security/incidents", query_string={"timeRange": "7d"}
        )
        pprint(resp.json)


if __name__ == "__main__":
    fetch_security_snapshots()


