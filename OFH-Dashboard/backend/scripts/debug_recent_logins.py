#!/usr/bin/env python3
"""Print recent logins from UserRepository for debugging."""

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


def dump_recent_logins(hours: int = 168, limit: int = 50):
    with get_session_context() as session:
        repo = UserRepository(session)
        users = repo.get_recent_logins(hours, limit)
        print(f"Recent logins returned: {len(users)}")
        for user in users:
            print(user.username, user.role, user.last_login)


if __name__ == "__main__":
    dump_recent_logins()


