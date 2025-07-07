from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sync import get_current_user
from database import get_db
from models import SyncData
from collections import defaultdict

router = APIRouter()

@router.get("")
def get_app_usage(since_minutes: int = Query(1440), db: Session = Depends(get_db), user=Depends(get_current_user)):
    cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)

    logs = db.query(SyncData).filter(
        SyncData.user_id == user.id,
        SyncData.date >= cutoff.date()
    ).all()

    usage = defaultdict(int)
    for log in logs:
        if log.app_usage:
            for app, minutes in log.app_usage.items():
                usage[app] += minutes

    return usage
