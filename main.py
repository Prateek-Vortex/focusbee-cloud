from fastapi import FastAPI
from auth import router as auth_router
import chat
from sync import router as sync_router
from database import engine, Base
from focus import router as focus_router
from app_usage import router as app_usage_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(auth_router, prefix="/auth")
app.include_router(sync_router, prefix="/sync")
app.include_router(focus_router, prefix="/focus")
app.include_router(chat.router, prefix="/chat")
app.include_router(app_usage_router, prefix="/app-usage")
