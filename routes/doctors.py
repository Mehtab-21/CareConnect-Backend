from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
import models
import json

router = APIRouter()

# ==========================================
# 1. FIND DOCTORS - CORRECT VAPI FORMAT
# ==========================================
@router.post("/find_doctors")
async def find_doctors(payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print(f"📦 INCOMING REQUEST")
    print(f"{'='*50}")
    print(json.dumps(payload, indent=2))

    try:
        # Extract toolCallId and arguments
        tool_call_id = None
        arguments = {}
        
        if "message" in payload and "toolCalls" in payload["message"]:
            tool_call = payload["message"]["toolCalls"][0]
            tool_call_id = tool_call["id"]
            args = tool_call["function"]["arguments"]
            arguments = json.loads(args) if isinstance(args, str) else args
        
        specialization = arguments.get("specialization", "").strip()
        location = arguments.get("location", "").strip()
        
        print(f"\n🔍 PARSED DATA:")
        print(f"   Tool Call ID: {tool_call_id}")
        print(f"   Specialization: {specialization}")
        print(f"   Location: {location}")

        # Database Query
        query = db.query(models.Doctor)

        if specialization:
            query = query.filter(models.Doctor.specialization.ilike(f"%{specialization}%"))
        
        if location:
            if location.lower() in ["nyc", "new york city", "ny"]:
                location = "New York"
            
            query = query.filter(
                or_(
                    models.Doctor.city.ilike(f"%{location}%"),
                    models.Doctor.zipcode == location,
                    models.Doctor.hospital.ilike(f"%{location}%")
                )
            )
        
        results = query.limit(3).all()
        print(f"\n📊 DATABASE RESULTS: Found {len(results)} doctors")
        for doc in results:
            print(f"   - Dr. {doc.name} ({doc.specialization}) in {doc.city}")

        # Build response - single line string
        if not results:
            result_text = f"I couldn't find any {specialization}s in {location}."
        else:
            doctor_list = []
            for doc in results:
                doctor_list.append(f"Dr. {doc.name}, {doc.specialization} in {doc.city}")
            result_text = "I found: " + "; ".join(doctor_list) + "."
        
        # Build response object according to Vapi docs
        response_obj = {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": result_text
                }
            ]
        }
        
        print(f"\n✅ SENDING RESPONSE:")
        print(json.dumps(response_obj, indent=2))
        print(f"{'='*50}\n")

        # Return with explicit JSON response
        return JSONResponse(content=response_obj, status_code=200)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = {
            "results": [
                {
                    "toolCallId": tool_call_id if tool_call_id else "unknown",
                    "result": "I had trouble searching. Please try again."
                }
            ]
        }
        return JSONResponse(content=error_response, status_code=200)
