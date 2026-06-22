"""
Railway Static Outbound IP Test Worker

Purpose:
- Runs continuously on Railway.
- Checks the public outbound IP every N seconds.
- Prints the IP in Railway logs.
- Optionally compares it with EXPECTED_STATIC_IP.

This is only a test script. Do not place real trades from this file.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone

import requests


CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
EXPECTED_STATIC_IP = os.getenv("EXPECTED_STATIC_IP", "").strip()

IPIFY_URL = "https://api.ipify.org?format=json"

shutdown_requested = False


def ist_now_str() -> str:
    """Return current IST time as readable string."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")


def handle_shutdown(signum, frame) -> None:
    """Handle Railway container shutdown gracefully."""
    global shutdown_requested
    shutdown_requested = True
    print(f"[{ist_now_str()}] Shutdown signal received: {signum}", flush=True)


def get_public_ip() -> str:
    """Fetch public outbound IP using api.ipify.org."""
    response = requests.get(IPIFY_URL, timeout=15)
    response.raise_for_status()
    data = response.json()
    return str(data["ip"]).strip()


def main() -> None:
    print("=" * 70, flush=True)
    print("Railway Static Outbound IP Test Started", flush=True)
    print(f"Start time      : {ist_now_str()}", flush=True)
    print(f"Check interval  : {CHECK_INTERVAL_SECONDS} seconds", flush=True)
    print(f"Expected IP     : {EXPECTED_STATIC_IP or '(not configured)'}", flush=True)
    print("=" * 70, flush=True)

    while not shutdown_requested:
        try:
            public_ip = get_public_ip()

            if EXPECTED_STATIC_IP:
                status = "MATCH" if public_ip == EXPECTED_STATIC_IP else "MISMATCH"
            else:
                status = "NO_EXPECTED_IP_SET"

            print(
                f"[{ist_now_str()}] outbound_ip={public_ip} status={status}",
                flush=True,
            )

        except Exception as exc:
            print(
                f"[{ist_now_str()}] ERROR while checking outbound IP: {type(exc).__name__}: {exc}",
                flush=True,
            )

        time.sleep(CHECK_INTERVAL_SECONDS)

    print(f"[{ist_now_str()}] Worker exiting cleanly.", flush=True)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        main()
    except Exception as exc:
        print(f"FATAL ERROR: {type(exc).__name__}: {exc}", flush=True)
        sys.exit(1)
