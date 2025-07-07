from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
from sqlalchemy.orm import Session
from openai import OpenAI
from sync import get_current_user
from database import get_db
from models import User

router = APIRouter()
client = OpenAI()

class ReminderRequest(BaseModel):
    app_usage: Dict[str, float]  # e.g., {"Chrome": 80.5, "Slack": 20.2}

@router.post("/focus/reminder-tip")
def generate_reminder_tip(
    req: ReminderRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    usage_summary = ", ".join(f"{app} for {minutes:.1f} mins" for app, minutes in req.app_usage.items())
    prompt = (
        f"Suggest a short, friendly wellness reminder for someone using these apps: {usage_summary}. "
        "Focus on hydration, posture, screen breaks, or stretch tips. Keep it casual and emoji-friendly."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a health-focused assistant that gives gentle wellness reminders."},
            {"role": "user", "content": prompt}
        ]
    )

    return {"reminder": response.choices[0].message.content.strip()}
