#!/usr/bin/env python3
"""
Utility script to launch the external alerting service stub.

Usage:
    python backend/scripts/run_alerting_stub.py
"""

import logging
import time
import sys
from pathlib import Path

from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Ensure repo root (for shared package) is importable
REPO_ROOT = BACKEND_ROOT.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(dotenv_path=BACKEND_ROOT / ".env", override=False)

from services.alerting import ExternalAlertingService


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    service = ExternalAlertingService()
    service.start(background=True)

    logging.info("External alerting stub is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping external alerting stub...")
        service.stop()


if __name__ == "__main__":
    main()