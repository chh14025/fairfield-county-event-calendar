from datetime import datetime

import icalendar
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Event
from ..schemas import EventDetailOut, EventListOut
from ..utils import utcnow

router = APIRouter()


def _filtered_query(
    db: Session,
    town: list[str] | None,
    from_: datetime | None,
    to: datetime | None,
    q: str | None,
    free_only: bool,
):
    query = db.query(Event).filter(Event.status == "approved")
    query = query.filter(Event.starts_at >= (from_ or utcnow()))
    if to:
        query = query.filter(Event.starts_at <= to)
    if town:
        query = query.filter(Event.town.in_(town))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Event.title.ilike(like), Event.description.ilike(like)))
    if free_only:
        query = query.filter(Event.price_text.ilike("%free%"))
    return query.order_by(Event.starts_at)


@router.get("/events", response_model=EventListOut)
def list_events(
    db: Session = Depends(get_db),
    town: list[str] | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    q: str | None = None,
    free_only: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),  # TODO(SPEC 7): cursor pagination before dataset grows
):
    query = _filtered_query(db, town, from_, to, q, free_only)
    total = query.count()
    items = query.limit(limit).offset(offset).all()
    return EventListOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/events.ics")
def events_ics(
    db: Session = Depends(get_db),
    town: list[str] | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    q: str | None = None,
    free_only: bool = False,
):
    events = _filtered_query(db, town, from_, to, q, free_only).limit(500).all()
    cal = icalendar.Calendar()
    cal.add("prodid", "-//Fairfield County Events//EN")
    cal.add("version", "2.0")
    for e in events:
        ve = icalendar.Event()
        ve.add("uid", f"{e.id}@fairfieldcountyevents")
        ve.add("summary", e.title)
        ve.add("dtstart", e.starts_at)
        if e.ends_at:
            ve.add("dtend", e.ends_at)
        if e.venue_name or e.address:
            ve.add("location", ", ".join(filter(None, [e.venue_name, e.address, e.town])))
        if e.description:
            ve.add("description", e.description)
        if e.url:
            ve.add("url", e.url)
        cal.add_component(ve)
    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=fairfield-events.ics"},
    )


@router.get("/events/{event_id}", response_model=EventDetailOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None or event.status not in ("approved", "expired"):
        raise HTTPException(status_code=404, detail="Event not found")
    return event
