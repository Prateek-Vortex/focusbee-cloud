from pydantic import BaseModel, EmailStr
from datetime import date

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class SyncUpload(BaseModel):
    date: date
    app_usage: dict[str, float]
    reminders_sent: int

class SyncResponse(SyncUpload):
    pass
