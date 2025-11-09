#!/usr/bin/env python3
"""Quick diagnostic for analytics endpoints."""

import os
from pathlib import Path
from pprint import pprint

from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv()

from core.database import get_session_context
from services.analytics_service import AnalyticsService


def dump_alert_metrics(time_range: str = "7d"):
    with get_session_context() as session:
        service = AnalyticsService(session)
        alert_data = service.get_alert_analytics(time_range)
        print("=== Alert Analytics ===")
        pprint(alert_data)

        response_data = service.get_response_times_analytics(time_range)
        print("\n=== Response Times Analytics ===")
        pprint(response_data)

        conversation_data = service.get_conversation_analytics(time_range)
        print("\n=== Conversation Analytics ===")
        pprint(conversation_data)


if __name__ == "__main__":
    dump_alert_metrics()


