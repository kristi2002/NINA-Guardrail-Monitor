#!/usr/bin/env python3
"""Inspect access trend buckets, including admin activity counts."""

from datetime import datetime, timezone
from collections import defaultdict
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_session_context
from repositories.user_repository import UserRepository
from api.routes.security import _bucket_to_hour, _ensure_datetime


def dump_access_trends(hours: int = 168, limit: int = 50):
    with get_session_context() as session:
        user_repo = UserRepository(session)
        recent_users = user_repo.get_recent_logins(hours, limit)

        trend_buckets = defaultdict(lambda: {
            'timestamp': None,
            'successful_logins': 0,
            'failed_logins': 0,
            'admin_activity': 0
        })
        admin_count = 0

        for user in recent_users:
            login_dt = _ensure_datetime(user.last_login) or datetime.now(timezone.utc)
            bucket_key = _bucket_to_hour(login_dt).isoformat()
            bucket = trend_buckets[bucket_key]
            bucket['timestamp'] = bucket_key
            bucket['successful_logins'] += 1
            if (user.role or '').lower() == 'admin':
                bucket['admin_activity'] += 1
                admin_count += 1

        print(f"Recent users returned: {len(recent_users)}")
        print(f"Admin activity count: {admin_count}")
        print("Trend buckets:")
        for bucket in sorted(trend_buckets.values(), key=lambda item: item['timestamp']):
            print(bucket)


if __name__ == "__main__":
    dump_access_trends()


