import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..db import get_db
from ..models import Tip
from ..schemas import TipIn, TipOut

router = APIRouter()
log = logging.getLogger("tips")

_tips_by_ip: dict[str, list[float]] = defaultdict(list)
DAY_S = 86400
DAILY_LIMIT = 5


def _rate_limited(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _tips_by_ip[ip] if now - t < DAY_S]
    _tips_by_ip[ip] = recent
    if len(recent) >= DAILY_LIMIT:
        return True
    recent.append(now)
    return False


@router.post("/tips", response_model=TipOut, status_code=201)
def create_tip(body: TipIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if _rate_limited(ip):
        raise HTTPException(status_code=429, detail="Daily tip limit reached")
    tip = Tip(message=body.message, email=body.email)
    db.add(tip)
    db.commit()
    log.info("Tip received (ip=%s)", ip)
    return tip


@router.get("/admin/tips", response_model=list[TipOut], dependencies=[Depends(require_admin)])
def list_tips(db: Session = Depends(get_db)):
    return db.query(Tip).order_by(Tip.created_at.desc()).limit(200).all()
