"""Fetch residential-only sources from THIS machine and push them to the prod API.

CivicPlus sites (norwalkct.gov, norwalkpl.org, greenwichct.gov) block cloud IPs,
so the AWS server cannot fetch them. Run this from a home connection on a schedule.

Env vars:
  EVENTS_API_URL        e.g. https://ffctevents.us
  EVENTS_ADMIN_PASSWORD the ADMIN_PASSWORD of the deployment

Run: python -m ingest.push_remote  (from backend/)
"""
import logging
import os
import sys
import time
from pathlib import Path

import httpx
import yaml

from .connectors.ical_feed import ICalConnector
from .runner import CONNECTOR_TYPES, filter_events

log = logging.getLogger("push_remote")


def residential_sources() -> list[dict]:
    path = Path(__file__).parent / "sources.yaml"
    data = yaml.safe_load(path.read_text())
    return [
        s for s in data.get("sources", [])
        if s.get("enabled") and s.get("residential_only") and "VERIFY" not in s["url"]
    ]


def main() -> int:
    api = os.environ.get("EVENTS_API_URL", "").rstrip("/")
    password = os.environ.get("EVENTS_ADMIN_PASSWORD", "")
    if not api or not password:
        print("Set EVENTS_API_URL and EVENTS_ADMIN_PASSWORD environment variables.")
        return 2
    headers = {"Authorization": f"Bearer {password}"}
    failures = 0
    for cfg in residential_sources():
        try:
            connector = CONNECTOR_TYPES[cfg["type"]](cfg)
            events = filter_events(connector.fetch(), cfg.get("exclude_titles", []))
            payload = [e.model_dump(mode="json") for e in events]
            resp = httpx.post(
                f"{api}/api/v1/admin/ingest/{cfg['id']}",
                json=payload, headers=headers, timeout=60,
            )
            resp.raise_for_status()
            log.info("%s: pushed %d events -> %s", cfg["id"], len(payload), resp.json())
        except Exception as exc:  # noqa: BLE001 — per-source isolation
            failures += 1
            log.exception("%s failed: %s", cfg["id"], exc)
        time.sleep(2)
    return 1 if failures else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
