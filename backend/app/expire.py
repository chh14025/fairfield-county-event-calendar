"""Nightly job: mark past events expired (SPEC 4). Run: python -m app.expire"""
from .db import SessionLocal, init_db
from .models import Event
from .utils import utcnow


def run() -> int:
    init_db()
    db = SessionLocal()
    try:
        n = (
            db.query(Event)
            .filter(Event.status == "approved", Event.starts_at < utcnow())
            .update({Event.status: "expired"})
        )
        db.commit()
        return n
    finally:
        db.close()


if __name__ == "__main__":
    print(f"expired {run()} events")
