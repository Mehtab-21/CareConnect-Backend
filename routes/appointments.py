from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import json

router = APIRouter()

# ==========================================
# 2. BOOK APPOINTMENT
# ==========================================

@router.post("/book_appointment")
async def book_appointment(payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print(f"📅 BOOKING REQUEST")
    print(f"{'='*50}")

    try:
        # 1. Parsing Vapi's Tool Call
        tool_call_id = None
        arguments = {}
        
        if "message" in payload and "toolCalls" in payload["message"]:
            tool_call = payload["message"]["toolCalls"][0]
            tool_call_id = tool_call["id"]
            args = tool_call["function"]["arguments"]
            # Handle cases where Vapi sends args as a string vs dict
            arguments = json.loads(args) if isinstance(args, str) else args
        
        # 2. Extract Data
        doctor_name = arguments.get("doctor_name", "").strip()
        patient_name = arguments.get("patient_name", "").strip()
        phone = arguments.get("phone", "").strip()
        appt_time = arguments.get("time", "").strip()
        appt_date = arguments.get("date", "Upcoming").strip() # Default if AI forgets date
        
        print(f"📋 Request: {patient_name} ({phone}) -> Dr. {doctor_name} @ {appt_date} {appt_time}")
        
        # 3. Validation: Find the Doctor (REAL ID LOOKUP)
        doctor = db.query(models.Doctor).filter(
            models.Doctor.name.ilike(f"%{doctor_name}%")
        ).first()
        
        if not doctor:
            return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": f"I couldn't find a doctor named {doctor_name}. Please ask for a different doctor."
                }]
            })

        # 4. MVP Feature: Availability Check (Prevent Double Booking)
        # Check if this doctor already has an appointment at this date/time
        existing_appt = db.query(models.Appointment).filter(
            models.Appointment.doctor_id == doctor.id,
            models.Appointment.appointment_date == appt_date,
            models.Appointment.appointment_time == appt_time
        ).first()

        if existing_appt:
             return JSONResponse(content={
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": f"Dr. {doctor.name} is actually fully booked at {appt_time}. Would you like to try a different time?"
                }]
            })

        # 5. Client Handling (Get Real ID or Create New)
        client = db.query(models.Client).filter(models.Client.phone == phone).first()
        
        if not client:
            print(f"👤 New Client Detected: {patient_name}")
            client = models.Client(name=patient_name, phone=phone)
            db.add(client)
            db.commit()
            db.refresh(client) # This populates client.id
        else:
            print(f"👤 Existing Client Found: ID {client.id}")

        # 6. Create Appointment (Using REAL IDs)
        new_appt = models.Appointment(
            client_id=client.id,     # Foreign Key to Clients table
            doctor_id=doctor.id,     # Foreign Key to Doctors table
            appointment_date=appt_date,
            appointment_time=appt_time,
            status="confirmed"
        )
        db.add(new_appt)
        db.commit()

        result_text = f"Success! I've booked {patient_name} with Dr. {doctor.name} for {appt_date} at {appt_time}."
        print(f"✅ Booking ID: {new_appt.id} Created")
        
        return JSONResponse(content={
            "results": [{
                "toolCallId": tool_call_id,
                "result": result_text
            }]
        })
        
    except Exception as e:
        print(f"❌ Booking error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={
            "results": [{
                "toolCallId": tool_call_id if tool_call_id else "unknown",
                "result": "I encountered a technical issue while booking. Please try again."
            }]
        })
