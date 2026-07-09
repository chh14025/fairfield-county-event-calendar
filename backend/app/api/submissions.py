import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Event, EventSource
from ..schemas import ModerationOut, SubmissionIn

router = APIRouter()
log = logging.getLogger("submissions")

# In-memory per-IP rate limit (SPEC 6). Move to Redis if we ever run >1 process.
_submissions_by_ip: dict[str, list[float]] = defaultdict(list)
DAY_S = 86400


def _rate_limited(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _submissions_by_ip[ip] if now - t < DAY_S]
    _submissions_by_ip[ip] = recent
    if len(recent) >= settings.submission_daily_limit:
        return True
    recent.append(now)
    return False


@router.post("/submissions", response_model=ModerationOut, status_code=201)
def create_submission(body: SubmissionIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if body.hp_field:  # honeypot filled -> bot; pretend success but store nothing
        log.warning("Honeypot tripped (ip=%s) — submission silently dropped", ip)
        return ModerationOut(id="ok", status="pending")
    if _rate_limited(ip):
        raise HTTPException(status_code=429, detail="Daily submission limit reached")

    event = Event(
        **body.model_dump(exclude={"hp_field"}),
        status="pending",
    )
    db.add(event)
    db.flush()
    db.add(
        EventSource(
            event_id=event.id,
            source_id="user-submission",
            external_id=event.id,
            raw=body.model_dump(mode="json", exclude={"hp_field"}),
        )
    )
    db.commit()
    log.info("Submission stored: %r (id=%s, ip=%s)", event.title, event.id, ip)
    return ModerationOut(id=event.id, status=event.status)
