from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import json
import dateparser
from datetime import datetime

router = APIRouter()

@router.post("/book_appointment")
async def book_appointment(payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print(f"📅 BOOKING REQUEST")
    
    try:
        # 1. Parse Vapi Payload
        tool_call_id = None
        args = {}
        if "message" in payload and "toolCalls" in payload["message"]:
            tool_call = payload["message"]["toolCalls"][0]
            tool_call_id = tool_call["id"]
            raw_args = tool_call["function"]["arguments"]
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        
        print(f"📥 RAW ARGS: {args}")

        # 2. Extract Data
        # Doctor Name Matching Strategy: Split name to find matches (e.g. "Lee" matches "Sarah Lee")
        doc_input = args.get("doctor_name", "").strip().replace("Dr.", "").strip()
        
        patient_name = args.get("patient_name", "Unknown").strip()
        phone = args.get("phone", "").strip()
        
        raw_date = args.get("date", "today")
        raw_time = args.get("time", "")

        # 3. DATE & TIME PROCESSING (The Fix)
        # Combine "next Wednesday" + "4 PM" -> "2025-11-12 16:00:00"
        dt_string = f"{raw_date} {raw_time}"
        parsed_dt = dateparser.parse(dt_string, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()})
        
        if parsed_dt:
            final_date_str = parsed_dt.strftime("%Y-%m-%d") # Database Standard: 2025-11-12
            final_time_str = parsed_dt.strftime("%H:%M")     # Database Standard: 16:00
            
            # Nice format for the voice agent to say back
            voice_confirm_date = parsed_dt.strftime("%A, %B %d") 
            voice_confirm_time = parsed_dt.strftime("%I:%M %p")
        else:
            # Fallback (Safety net)
            final_date_str = datetime.now().strftime("%Y-%m-%d")
            final_time_str = raw_time
            voice_confirm_date = raw_date
            voice_confirm_time = raw_time

        # 4. Find Doctor (Improved Logic)
        # We try to match the last name if full name fails
        doctor = db.query(models.Doctor).filter(models.Doctor.name.ilike(f"%{doc_input}%")).first()
        
        if not doctor:
            # Try searching just by last word (e.g. user said "Lee", DB has "Sarah Lee")
            last_name = doc_input.split()[-1]
            doctor = db.query(models.Doctor).filter(models.Doctor.name.ilike(f"%{last_name}%")).first()

        if not doctor:
            return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": f"I couldn't find a doctor named {doc_input}. Please confirm the doctor's full name."
                }]
            })

        # 5. Handle Client (Create or Find)
        client = db.query(models.Client).filter(models.Client.phone == phone).first()
        if not client:
            client = models.Client(name=patient_name, phone=phone)
            db.add(client)
            db.commit()
            db.refresh(client)

        # 6. Create Appointment
        new_appt = models.Appointment(
            client_id=client.id,
            doctor_id=doctor.id,
            appointment_date=final_date_str, # Now stores "2025-11-12"
            appointment_time=final_time_str, # Now stores "16:00"
            status="confirmed"
        )
        db.add(new_appt)
        db.commit()

        print(f"✅ BOOKED: Dr. {doctor.name} | {final_date_str} @ {final_time_str}")

        return JSONResponse(content={
            "results": [{
                "toolCallId": tool_call_id,
                "result": f"Success. I have confirmed your appointment with Dr. {doctor.name} for {voice_confirm_date} at {voice_confirm_time}."
            }]
        })

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return JSONResponse(content={"results": [{"toolCallId": tool_call_id, "result": "System error booking appointment."}]})