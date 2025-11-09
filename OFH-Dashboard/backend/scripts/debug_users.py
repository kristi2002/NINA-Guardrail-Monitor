#!/usr/bin/env python3
"""Print user roles and last_login values for debugging."""

import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_session_context
from models.user import User


def dump_users():
    with get_session_context() as session:
        users = session.query(User).order_by(User.username).all()
        for user in users:
            print(
                f"{user.username:30s} role={user.role:<10s} "
                f"last_login={user.last_login} attempts={user.login_attempts}"
            )


if __name__ == "__main__":
    dump_users()


