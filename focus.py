from datetime import date
from sqlalchemy.orm import Session
from fastapi import Depends
from sync import get_current_user
from database import get_db
from models import User, SyncData
from openai import OpenAI, api_key
from collections import Counter
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date as Date
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
router = APIRouter()

@router.get("/me/focus-summary")
def focus_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = generate_focus_summary(db, user)
    return {"summary": summary}

def generate_focus_summary(db: Session, user: User) -> str:
    today = date.today()
    logs = db.query(SyncData).filter(
        SyncData.user_id == user.id,
        SyncData.date == today
    ).first()

    if not logs:
        return "No activity data found for today."

    usage = logs.app_usage or {}
    total_minutes = sum(usage.values())
    idle_events = logs.reminders_sent  # reuse this field for now

    top_apps = Counter(usage).most_common(3)
    usage_summary = ", ".join(f"{app} ({mins} min)" for app, mins in top_apps)

    prompt = f"""
    Here's the user's productivity log:
    - Total active minutes: {total_minutes}
    - Reminders triggered (idle/breaks): {idle_events}
    - Most used apps: {usage_summary}

    Write a short 2-3 sentence natural language productivity summary. Include encouragement and one improvement suggestion.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a friendly productivity assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()




class ReminderRequest(BaseModel):
    app_usage: Optional[dict] = None

@router.post("/reminder-tip")
def get_reminder_tip(
    payload: ReminderRequest = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app_usage = payload.app_usage if payload and payload.app_usage else None

    if not app_usage:
        today = Date.today()
        sync = (
            db.query(SyncData)
            .filter(SyncData.user_id == user.id, SyncData.date == today)
            .first()
        )
        if sync:
            app_usage = sync.app_usage
        else:
            app_usage = {}

    # Turn app_usage into a readable summary
    summary = (
        "Today's app usage:\n" +
        "\n".join([f"- {app}: {mins} minutes" for app, mins in app_usage.items()])
        if app_usage else
        "No app usage data available for today."
    )

    prompt = (
        f"{summary}\n\n"
        "Based on this usage, suggest a wellness reminder or motivational tip. "
        "Make it light, positive, and context-aware like: 'Drink water 💧', or "
        "'You've been on Chrome too long — take a 5-min stretch!'"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a playful wellness coach who gives positive focus reminders."},
            {"role": "user", "content": prompt}
        ]
    )

    return { "tip": response.choices[0].message.content.strip() }

