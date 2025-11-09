#!/usr/bin/env python3
"""Print recent admin activity metrics from AnalyticsService."""

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


def dump_admin_activity():
    with get_session_context() as session:
        service = AnalyticsService(session)
        metrics = service._get_user_activity_metrics(168, admin_only=True)
        activity = metrics.get('recent_activity', [])
        print(f"Recent activity buckets (direct): {len(activity)}")
        pprint(activity[:10])
        response = service.get_user_analytics('7d', admin_only=True)
        data = response.get('data', {})
        perf_metrics = data.get('performance_metrics', {})
        response_activity = perf_metrics.get('recent_activity', [])
        print(f"Recent activity buckets (via API): {len(response_activity)}")
        pprint(response_activity[:10])


if __name__ == "__main__":
    dump_admin_activity()


