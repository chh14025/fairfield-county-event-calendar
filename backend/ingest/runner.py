"""Ingestion runner: loads sources.yaml, fetches each enabled source, upserts with dedup.

Run: python -m ingest.runner  (from backend/)
Per SPEC 3: a failing source never aborts the run; every run is recorded in IngestRun.
"""
import logging
import time
from pathlib import Path

import yaml

from app.db import SessionLocal, init_db
from app.dedup import upsert_event
from app.models import IngestRun
from app.utils import utcnow

from .connectors.ical_feed import ICalConnector

log = logging.getLogger("ingest")

CONNECTOR_TYPES = {
    "ical": lambda cfg: ICalConnector(cfg["id"], cfg["url"], cfg.get("town", "Other")),
}

PER_SOURCE_DELAY_S = 2  # politeness between sources


def load_sources(path: Path | None = None) -> list[dict]:
    path = path or Path(__file__).parent / "sources.yaml"
    data = yaml.safe_load(path.read_text())
    # residential_only sources are fetched by ingest/push_remote.py from a home
    # connection (CivicPlus blocks cloud IPs) and pushed via the admin API.
    return [
        s for s in data.get("sources", [])
        if s.get("enabled") and not s.get("residential_only")
    ]


def filter_events(events: list, exclude_titles: list[str]) -> list:
    """Drop events whose title contains any excluded phrase (case-insensitive).
    Used for calendar noise like 'Library Closed' notices."""
    if not exclude_titles:
        return events
    patterns = [p.lower() for p in exclude_titles]
    kept = [e for e in events if not any(p in e.title.lower() for p in patterns)]
    dropped = len(events) - len(kept)
    if dropped:
        log.info("filtered %d excluded-title events", dropped)
    return kept


def run(sources: list[dict] | None = None) -> None:
    init_db()
    sources = sources if sources is not None else load_sources()
    if not sources:
        log.warning("No enabled sources in sources.yaml — nothing to do.")
        return
    for cfg in sources:
        db = SessionLocal()
        run_row = IngestRun(source_id=cfg["id"])
        db.add(run_row)
        db.commit()
        try:
            connector = CONNECTOR_TYPES[cfg["type"]](cfg)
            raw_events = filter_events(connector.fetch(), cfg.get("exclude_titles", []))
            for raw in raw_events:
                upsert_event(db, raw, source_id=cfg["id"])
            db.commit()
            run_row.ok = True
            run_row.events_found = len(raw_events)
            log.info("%s: %d events", cfg["id"], len(raw_events))
        except Exception as exc:  # noqa: BLE001 — isolate per-source failures (SPEC 3)
            db.rollback()
            run_row.error = str(exc)[:2000]
            log.exception("%s failed", cfg["id"])
        finally:
            run_row.finished_at = utcnow()
            db.commit()
            db.close()
        time.sleep(PER_SOURCE_DELAY_S)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
