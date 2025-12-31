from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

# ==========================================
# 3. CALL LOGS
# ==========================================
@router.post("/save_call_log")
async def save_call_log(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        print("📞 Saving call log...")

        message = payload.get("message", {})
        call_analysis = message.get("analysis", {})
        
        summary = call_analysis.get("summary", "No summary")
        transcript = message.get("transcript", "")
        customer_number = message.get("customer", {}).get("number", "Unknown")

        log = models.CallLog(
            caller_number=customer_number,
            summary=summary,
            transcript=transcript,
            vapi_data=payload
        )
        db.add(log)
        db.commit()
        
        print("✅ Call log saved")
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Log error: {e}")
        return {"status": "error"}
