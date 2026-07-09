from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ingest.connectors.base import RawEvent

from ..auth import login, require_admin
from ..dedup import upsert_event
from ..utils import utcnow
from ..db import get_db
from ..models import Event, IngestRun
from ..schemas import EventOut, LoginIn, ModerationOut, PendingEventOut, RejectIn

router = APIRouter(prefix="/admin")


@router.post("/login")
def admin_login(body: LoginIn, request: Request, response: Response):
    login(request, response, body.password)
    return {"ok": True}


@router.get("/pending", response_model=list[PendingEventOut], dependencies=[Depends(require_admin)])
def pending(db: Session = Depends(get_db)):
    return (
        db.query(Event)
        .filter(Event.status == "pending")
        .order_by(Event.created_at)
        .all()
    )


def _moderate(db: Session, event_id: str, new_status: str) -> Event:
    event = db.get(Event, event_id)
    if event is None or event.status != "pending":
        raise HTTPException(status_code=404, detail="No such pending event")
    event.status = new_status
    db.commit()
    return event


@router.post(
    "/events/{event_id}/approve",
    response_model=ModerationOut,
    dependencies=[Depends(require_admin)],
)
def approve(event_id: str, db: Session = Depends(get_db)):
    e = _moderate(db, event_id, "approved")
    return ModerationOut(id=e.id, status=e.status)


@router.post(
    "/events/{event_id}/reject",
    response_model=ModerationOut,
    dependencies=[Depends(require_admin)],
)
def reject(event_id: str, body: RejectIn | None = None, db: Session = Depends(get_db)):
    e = _moderate(db, event_id, "rejected")
    if body and body.reason:
        e.rejection_reason = body.reason
        db.commit()
    return ModerationOut(id=e.id, status=e.status)


@router.delete(
    "/events/{event_id}",
    response_model=ModerationOut,
    dependencies=[Depends(require_admin)],
)
def remove(event_id: str, db: Session = Depends(get_db)):
    """Remove any event from the site (pending, approved, or expired).

    Implemented as status=rejected rather than a hard delete: the EventSource
    rows survive, so the next ingest run updates the event in place instead of
    resurrecting it as a fresh approved copy.
    """
    event = db.get(Event, event_id)
    if event is None or event.status == "rejected":
        raise HTTPException(status_code=404, detail="No such event")
    event.status = "rejected"
    db.commit()
    return ModerationOut(id=event.id, status=event.status)


@router.post("/ingest/{source_id}", dependencies=[Depends(require_admin)])
def ingest_push(source_id: str, events: list[RawEvent], db: Session = Depends(get_db)):
    """Receive pre-parsed events from a trusted remote runner (home connection).

    Used for sources whose feeds block cloud IPs (CivicPlus: Norwalk, Greenwich .gov).
    Same upsert/dedup path as server-side ingestion.
    """
    if len(events) > 2000:
        raise HTTPException(status_code=413, detail="Too many events in one push")
    run_row = IngestRun(source_id=source_id, ok=True, events_found=len(events))
    db.add(run_row)
    actions = {"created": 0, "updated": 0, "merged": 0}
    for raw in events:
        _, action = upsert_event(db, raw, source_id=source_id)
        actions[action] += 1
    run_row.finished_at = utcnow()
    db.commit()
    return {"received": len(events), **actions}


@router.get("/ingest-runs", dependencies=[Depends(require_admin)])
def ingest_runs(db: Session = Depends(get_db)):
    rows = db.query(IngestRun).order_by(IngestRun.started_at.desc()).limit(50).all()
    return [
        {
            "source_id": r.source_id,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "ok": r.ok,
            "events_found": r.events_found,
            "error": r.error,
        }
        for r in rows
    ]
