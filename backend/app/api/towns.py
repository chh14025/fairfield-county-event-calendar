from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import TOWNS, Event
from ..schemas import TownCount
from ..utils import utcnow

router = APIRouter()


@router.get("/towns", response_model=list[TownCount])
def list_towns(db: Session = Depends(get_db)):
    counts = dict(
        db.query(Event.town, func.count(Event.id))
        .filter(Event.status == "approved", Event.starts_at >= utcnow())
        .group_by(Event.town)
        .all()
    )
    return [TownCount(town=t, upcoming_events=counts.get(t, 0)) for t in TOWNS]
