from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from models import User
from schemas import UserCreate, UserLogin, TokenResponse
from database import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import uuid
import threading


auth_codes = {}
auth_codes_lock = threading.Lock()



router = APIRouter()
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET", "secret123")

# --- Auth Core ---

@router.post("/register", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hash(user.password)
    new_user = User(email=user.email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return create_token(new_user.id)

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    print(data)
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not bcrypt.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_token(user.id)

def create_token(user_id: str):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# --- Deep Link Auth ---

@router.post("/generate-code")
def generate_code(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    code = str(uuid.uuid4())

    # Default: store in-memory (DEV)
    with auth_codes_lock:
        auth_codes[code] = token

    # Optional: also store in Redis
    #store_code_in_redis(code, token)

    return {"code": code}


class CodeInput(BaseModel):
    code: str

@router.post("/exchange-code")
def exchange_code(payload: CodeInput):
    code = payload.code

    # ✅ Thread-safe pop
    with auth_codes_lock:
        token = auth_codes.pop(code, None)

    # if not token:
    #     token = get_code_from_redis(code)
    #     if token:
    #         delete_code_from_redis(code)

    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    return {"access_token": token}


# --- Redis Helpers (template) ---

# To enable, install: pip install redis
# try:
#     import redis
#     redis_client = redis.Redis(host="localhost", port=6379, db=0)
# except ImportError:
#     redis_client = None


# def store_code_in_redis(code: str, token: str, expiry_seconds=60):
#     if redis_client:
#         redis_client.setex(f"auth_code:{code}", expiry_seconds, token)

# def get_code_from_redis(code: str):
#     if redis_client:
#         value = redis_client.get(f"auth_code:{code}")
#         return value.decode() if value else None

# def delete_code_from_redis(code: str):
#     if redis_client:
#         redis_client.delete(f"auth_code:{code}")
