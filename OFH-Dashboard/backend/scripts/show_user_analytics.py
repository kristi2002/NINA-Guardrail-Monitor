#!/usr/bin/env python3
"""Print user analytics response for debugging."""

import os
from pathlib import Path
from pprint import pprint

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv()

from core.database import get_session_context
from services.analytics_service import AnalyticsService


def show_user_analytics(time_range: str = '7d', admin_only: bool = True):
    with get_session_context() as session:
        service = AnalyticsService(session)
        response = service.get_user_analytics(time_range, admin_only=admin_only)
        pprint(response)


if __name__ == "__main__":
    show_user_analytics()


