from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, SyncData
from schemas import SyncUpload, SyncResponse
from jose import jwt, JWTError
import os
from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID

router = APIRouter()
SECRET_KEY = os.getenv("JWT_SECRET", "secret123")

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = UUID(payload.get("sub"))  # ✅ convert string to UUID
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/", response_model=dict)
def upload_sync(data: SyncUpload, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sync = SyncData(user_id=user.id, date=data.date, app_usage=data.app_usage, reminders_sent=data.reminders_sent)
    db.add(sync)
    db.commit()
    return {"status": "ok"}

@router.get("/", response_model=list[SyncResponse])
def fetch_sync(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SyncData).filter_by(user_id=user.id).all()
