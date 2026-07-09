"""Probe every source in sources.yaml (including disabled) and report feed health.

Run locally: python -m ingest.verify_sources
For each source: fetches via the same connector the runner uses; prints event count or error.
Meant to be run from a residential connection — some town sites block datacenter IPs.
"""
import sys
from pathlib import Path

import yaml

from .connectors.ical_feed import ICalConnector


def main() -> int:
    path = Path(__file__).parent / "sources.yaml"
    all_sources = yaml.safe_load(path.read_text())["sources"]
    failures = 0
    for cfg in all_sources:
        sid, url = cfg["id"], cfg["url"]
        if "VERIFY" in url:
            print(f"[skip]  {sid}: URL still has VERIFY placeholder")
            continue
        if cfg.get("type") != "ical":
            print(f"[skip]  {sid}: type={cfg.get('type')} (no connector yet)")
            continue
        try:
            connector = ICalConnector(sid, url, cfg.get("town", "Other"))
            events = connector.fetch()
            print(f"[ok]    {sid}: {len(events)} events parsed")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[fail]  {sid}: {type(exc).__name__}: {str(exc)[:120]}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
