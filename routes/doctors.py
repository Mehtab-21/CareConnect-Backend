from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
import models
import json

router = APIRouter()

# ==========================================
# 1. FIND DOCTORS (With Availability)
# ==========================================
@router.post("/find_doctors")
async def find_doctors(payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print(f"🔎 SEARCH REQUEST")
    
    try:
        # 1. Parse Args
        tool_call_id = None
        args = {}
        if "message" in payload and "toolCalls" in payload["message"]:
            tool_call = payload["message"]["toolCalls"][0]
            tool_call_id = tool_call["id"]
            raw_args = tool_call["function"]["arguments"]
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        
        # 2. Strict Extraction
        specialization = args.get("specialization", "").strip()
        
        # CHANGED: explicitly look for 'zip_code' now
        zip_code = args.get("zip_code") or args.get("location") or ""
        zip_code = zip_code.strip()
        
        print(f"🔍 Criteria: Spec='{specialization}' | Zip='{zip_code}'")

        # 3. Database Search (Strict Zip)
        query = db.query(models.Doctor)
        if specialization:
            query = query.filter(models.Doctor.specialization.ilike(f"%{specialization}%"))
        
        # STRICT ZIP MODE: Only search if we have a valid zip
        if zip_code and zip_code.isdigit() and len(zip_code) == 5:
            query = query.filter(models.Doctor.zipcode == zip_code)
        else:
            # If AI sent bad data, return a helper message instead of a fake search
            return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": "Please ask the user for their 5-digit zip code. I cannot search without it."
                }]
            })

        results = query.limit(3).all()

        # 4. Format Output for the AI
        if not results:
            result_text = f"No {specialization}s found in {zip_code}. Ask the user for a different zip code."
        else:
            # We build a script for the AI to read
            doc_lines = []
            for doc in results:
                # Format: "Monday (9am-5pm), Wednesday (2pm-6pm)"
                schedule = []
                if doc.availability:
                    for day, time in doc.availability.items():
                        schedule.append(f"{day} from {time}")
                    avail_str = ", ".join(schedule)
                else:
                    avail_str = "Standard Business Hours"
                
                doc_lines.append(f"Dr. {doc.name} ({doc.consultation_type}) is available: {avail_str}")
            
            # The AI reads this result text directly to the user
            result_text = "I found these doctors. " + ". ".join(doc_lines) + ". Which one would you like to book?"

        return JSONResponse(content={
            "results": [{
                "toolCallId": tool_call_id,
                "result": result_text
            }]
        })

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return JSONResponse(content={"results": [{"toolCallId": tool_call_id, "result": "System Error."}]})