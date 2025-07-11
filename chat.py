from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date as Date, date
from sqlalchemy.orm import Session
from database import get_db
from sync import get_current_user
from models import User, SyncData
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#client = OpenAI() # Assuming you use OpenAI API
router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    date: Optional[Date] = None

@router.post("")
def chat_with_focus_assistant(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_date = req.date or date.today()

    usage = (
        db.query(SyncData)
        .filter(SyncData.user_id == user.id, SyncData.date == target_date)
        .first()
    )

    context_summary = (
        f"User activity on {target_date}:\n"
        f"- Active time: {round(sum(usage.app_usage.values()), 1)} minutes\n"
        f"- Apps used: {', '.join(usage.app_usage.keys())}\n"
        f"- Reminders sent: {usage.reminders_sent}\n"
        if usage else
        "No usage data available for the day."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a friendly productivity coach."},
            {"role": "system", "content": context_summary},
            {"role": "user", "content": req.question}
        ]
    )

    return {"response": response.choices[0].message.content.strip()}

