from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import json
import dateparser # <--- Vital for converting "Tomorrow at 5" to actual dates

router = APIRouter()

@router.post("/book_appointment")
async def book_appointment(payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print(f"📅 INCOMING BOOKING REQUEST")
    
    try:
        # --- 1. ROBUST PARSING OF VAPI PAYLOAD ---
        tool_call_id = None
        args = {}
        
        # Safe extraction of tool calls
        if "message" in payload and "toolCalls" in payload["message"]:
            tool_call = payload["message"]["toolCalls"][0]
            tool_call_id = tool_call["id"]
            raw_args = tool_call["function"]["arguments"]
            
            # Handle cases where Vapi sends stringified JSON vs actual Dict
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        
        # 🔍 DEBUG: This shows exactly what Vapi is sending
        print(f"📥 RAW ARGS FROM VAPI: {args}") 

        # --- 2. EXTRACT DATA & HANDLE KEY VARIATIONS ---
        # Vapi might mix up keys like 'mobile' vs 'phone'. We check all options.
        
        doctor_name_input = args.get("doctor_name") or args.get("doctor") or ""
        patient_name_input = args.get("patient_name") or args.get("name") or "Unknown"
        phone_input = args.get("phone") or args.get("mobile") or args.get("number") or ""
        
        raw_date = args.get("date") or "today"
        raw_time = args.get("time") or ""

        # Clean whitespace
        doctor_name_input = doctor_name_input.strip()
        patient_name_input = patient_name_input.strip()
        phone_input = str(phone_input).strip()

        print(f"📝 PARSED: Patient='{patient_name_input}' ({phone_input}) -> Dr='{doctor_name_input}'")

        # --- 3. STANDARDIZE DATE & TIME ---
        # Combine them for smart parsing (e.g. "Tomorrow" + "10am")
        combined_string = f"{raw_date} {raw_time}"
        
        # settings={'PREFER_DATES_FROM': 'future'} ensures "Monday" means NEXT Monday
        parsed_dt = dateparser.parse(combined_string, settings={'PREFER_DATES_FROM': 'future'})
        
        if parsed_dt:
            # Format nicely for Database (ISO Format)
            final_date = parsed_dt.strftime("%Y-%m-%d")  # e.g., '2025-10-25'
            final_time = parsed_dt.strftime("%H:%M")     # e.g., '14:30'
            display_dt = parsed_dt.strftime('%A, %B %d at %I:%M %p') # For voice response
            print(f"🕒 Time Standardized: '{combined_string}' -> {final_date} at {final_time}")
        else:
            # Fallback if parsing fails
            print("⚠️ Could not parse date, using raw values.")
            final_date = raw_date
            final_time = raw_time
            display_dt = f"{raw_date} at {raw_time}"

        # --- 4. VALIDATION (The Guardrails) ---
        if not doctor_name_input:
            return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": "I didn't catch which doctor you want to see. Please specify the doctor's name."
                }]
            })

        if not phone_input or len(phone_input) < 5:
            return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": "I need a valid phone number to confirm the appointment. Could you please provide it?"
                }]
            })

        # --- 5. FIND DOCTOR (Strict Search) ---
        doctor = db.query(models.Doctor).filter(
            models.Doctor.name.ilike(f"%{doctor_name_input}%")
        ).first()
        
        if not doctor:
            print(f"❌ Doctor '{doctor_name_input}' not found.")
            return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": f"I couldn't find a doctor named {doctor_name_input}. Please confirm the name."
                }]
            })
            
        print(f"✅ Found Doctor: ID {doctor.id} ({doctor.name})")

        # --- 6. CHECK AVAILABILITY ---
        existing_appt = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.appointment_date == final_date,
            models.Appointment.appointment_time == final_time
        ).first()

        if existing_appt:
             return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": f"Dr. {doctor.name} is already booked at {final_time}. Please choose another time."
                }]
            })

        # --- 7. CLIENT HANDLING (Fixing the Missing Data Issue) ---
        client = db.query(models.Client).filter(models.Client.phone == phone_input).first()
        
        if not client:
            print(f"🆕 Creating New Client: {patient_name_input}")
            client = models.Client(name=patient_name_input, phone=phone_input)
            db.add(client)
            db.commit()
            db.refresh(client)
        else:
            print(f"👤 Existing Client Found: ID {client.id}")
            # Update name if previously unknown
            if (client.name == "Unknown" or not client.name) and patient_name_input != "Unknown":
                client.name = patient_name_input
                db.commit()

        # --- 8. CREATE APPOINTMENT (With CLEAN Date/Time) ---
        new_appt = models.Appointment(
            client_id=client.id,
            doctor_id=doctor.id,
            appointment_date=final_date,
            appointment_time=final_time,
            status="confirmed"
        )
        db.add(new_appt)
        db.commit()

        print(f"✅ Booking Success: Appt ID {new_appt.id}")

        return JSONResponse(content={
            "results": [{
                "toolCallId": tool_call_id,
                "result": f"Success! I have booked {patient_name_input} with Dr. {doctor.name} for {display_dt}."
            }]
        })

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "results": [{
                "toolCallId": tool_call_id if tool_call_id else "unknown",
                "result": "I encountered a technical issue while booking. Please try again later."
            }]
        })