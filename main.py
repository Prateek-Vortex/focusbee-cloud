from fastapi import FastAPI
from auth import router as auth_router
from sync import router as sync_router
from database import engine, Base
from focus import router as focus_router

app = FastAPI()

# Create all tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(auth_router, prefix="/auth")
app.include_router(sync_router, prefix="/sync")
app.include_router(focus_router, prefix="/focus")
