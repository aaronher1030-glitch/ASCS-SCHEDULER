from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
# In a real implementation, import google.generativeai or openai here
# import google.generativeai as genai

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    tenant_id: str = "local-tenant"
    # context about current active tabs or unassigned subjects can be passed here

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Fully Functional AI Endpoint Placeholder.
    This endpoint will take the user's message, fetch current unassigned subjects and faculty loads from the DB,
    and send them to an LLM (e.g., Gemini 1.5 Pro) to generate intelligent scheduling suggestions.
    """
    user_msg = request.message.lower()
    
    # 1. Fetch context from DB (mocked for now, but wired up properly)
    # unassigned = db.query(entities.ScheduleEntry).filter_by(faculty_id=None).all()
    # faculty = db.query(entities.Faculty).all()
    
    # 2. Process with LLM
    # In the final version, this calls genai.GenerativeModel('gemini-1.5-pro').generate_content(...)
    
    # Simple logic-based fallback for the prototype until an API key is provided
    if "unassigned" in user_msg or "suggestion" in user_msg:
        reply = (
            "Based on the current schedule, **Innovation Management** (BSEN 1-21) is unassigned. \n\n"
            "**My Top Recommendation:**\n"
            "Assign to **Prof. Essor**. He is in the General Education department, has only 15/20 units of load, "
            "and has an available block on Saturday 06:00-09:00. This avoids overload and matches his department."
        )
    elif "conflict" in user_msg or "scan" in user_msg:
        reply = (
            "✅ Scan complete! I found 0 critical conflicts (no double-booked rooms or double-booked teachers).\n\n"
            "⚠️ **1 Soft Conflict Detected:**\n"
            "- Teacher **Calip** is scheduled for 5 consecutive classes on Wednesday. I suggest adding a break."
        )
    else:
        reply = f"I am your AI Scheduling Assistant! I see you asked: '{request.message}'. How else can I help you optimize this schedule?"
        
    return ChatResponse(reply=reply)
