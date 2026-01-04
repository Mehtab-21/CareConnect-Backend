from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from database import get_db
import models
import json
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# ==========================================
# 1. FRONTEND DATA MODEL (DTO)
# Matches your Angular 'PatientRequest' interface
# ==========================================
class PatientRequestDTO(BaseModel):
    id: str
    patientName: str
    dateTime: datetime
    requestedSpecialty: Optional[str] = "General"
    symptoms: List[str]
    keyPhrases: List[str]          # Matches 'patient_quotes'
    extractedKeywords: List[str]   # Matches 'extracted_keywords'
    aiSummary: Optional[str]
    suggestedAction: Optional[str]
    status: str
    preferredLocation: Optional[str]
    contactPhone: Optional[str]
    urgencyLevel: str              # 'low' | 'medium' | 'high'
    fullTranscript: Optional[str]  # The full text block

    class Config:
        orm_mode = True

# ==========================================
# 2. GET ENDPOINT (For Angular Dashboard)
# ==========================================
@router.get("/patient_requests", response_model=List[PatientRequestDTO])
def get_patient_requests(db: Session = Depends(get_db)):
    """
    Fetches call logs, formats them, and sends them to the frontend.
    """
    # Fetch logs (newest first) and join with Client table
    logs = db.query(models.CallLog)\
        .options(joinedload(models.CallLog.client))\
        .order_by(desc(models.CallLog.created_at))\
        .all()

    response_data = []

    for log in logs:
        # Map Urgency Score (1-10) to labels
        score = log.urgency_score or 5
        if score >= 8: urgency = 'high'
        elif score >= 5: urgency = 'medium'
        else: urgency = 'low'

        # Helper to safely parse symptoms string into a list
        symptoms_list = [s.strip() for s in (log.symptoms or "").split(',')] if log.symptoms else []

        # Create the data object for the frontend
        dto = PatientRequestDTO(
            id=str(log.id),
            patientName=log.client.name if log.client else "Unknown",
            dateTime=log.created_at,
            requestedSpecialty=log.specialty or "General",
            symptoms=symptoms_list,
            
            # These JSON lists come directly from the DB
            keyPhrases=log.patient_quotes or [],
            extractedKeywords=log.extracted_keywords or [],
            
            aiSummary=log.summary,
            suggestedAction=log.ai_action_summary or "Review patient details.",
            status=log.status.lower() if log.status else "new",
            preferredLocation=log.client.zipcode if log.client else "",
            contactPhone=log.client.phone if log.client else "",
            urgencyLevel=urgency,
            fullTranscript=log.transcript
        )
        response_data.append(dto)

    return response_data

# ==========================================
# 3. POST ENDPOINT (Save Data from Vapi)
# ==========================================
@router.post("/save_call_log")
async def save_call_details(payload: dict = Body(...), db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print("📝 SAVING RICH CALL DATA...")

    try:
        # 1. Parse Tool Arguments
        tool_calls = payload.get("message", {}).get("toolCalls", [])
        if not tool_calls:
            return {"results": [{"result": "Error: No data received."}]}

        tool_call = tool_calls[0]
        args = tool_call.get("function", {}).get("arguments", {})
        
        # Handle JSON string parsing if needed
        if isinstance(args, str):
            args = json.loads(args)

        print(f"📥 Received for: {args.get('patient_name')}")

        # 2. Find or Create Client
        phone = args.get("patient_phone")
        # Fallback to caller ID if tool didn't send phone
        if not phone:
            phone = payload.get("message", {}).get("customer", {}).get("number", "Unknown")

        stmt = select(models.Client).where(models.Client.phone == phone)
        client = db.execute(stmt).scalars().first()

        if not client:
            client = models.Client(
                phone=phone,
                name=args.get("patient_name", "Unknown"),
                zipcode=args.get("location") # Using 'location' as generic field
            )
            db.add(client)
            db.commit()
            db.refresh(client)
        else:
            if args.get("patient_name"): client.name = args.get("patient_name")
            if args.get("location"): client.zipcode = args.get("location")
            db.commit()

        # 3. Create Rich Call Log
        new_log = models.CallLog(
            vapi_call_id=payload.get("message", {}).get("call", {}).get("id"),
            client_id=client.id,
            
            # Text Fields
            specialty=args.get("specialty"),
            summary=args.get("summary"),
            symptoms=args.get("symptoms"),
            transcript=args.get("transcript_summary"), # Storing the summary of transcript provided by AI
            ai_action_summary="Appointment details pending doctor review.", 
            
            # JSON Fields (Lists)
            patient_quotes=args.get("quotes", []),     # List of strings
            extracted_keywords=args.get("keywords", []), # List of strings
            
            urgency_score=args.get("urgency", 5),
            status="NEW"
        )

        db.add(new_log)
        db.commit()

        print(f"✅ SAVED PROFILE: {client.name} | {new_log.specialty}")

        return {
            "results": [
                {
                    "toolCallId": tool_call.get("id"),
                    "result": "Patient profile and summary saved successfully."
                }
            ]
        }

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {"results": [{"result": "System error saving profile."}]}