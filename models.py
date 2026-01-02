from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# =========================
# 1. ROLES
# =========================
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)
    users = relationship("User", back_populates="role")

# =========================
# 2. USERS (Internal Staff)
# =========================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(255), unique=True)
    password_hash = Column(String(255))
    role_id = Column(Integer, ForeignKey("roles.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    role = relationship("Role", back_populates="users")

# =========================
# 3. CLIENTS (The Callers)
# =========================
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    phone = Column(String(20), unique=True, index=True)
    email = Column(String(255), nullable=True)
    zipcode = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointments = relationship("Appointment", back_populates="client")
    call_logs = relationship("CallLog", back_populates="client")

# =========================
# 4. DOCTORS
# =========================

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100))
    hospital = Column(String(100))
    city = Column(String(50))
    zipcode = Column(String(10))
    
    languages = Column(JSON, nullable=True)
    insurance = Column(JSON, nullable=True)
    
    # --- NEW COLUMN ---
    availability = Column(JSON, nullable=True, default={}) 
    # Example format: {"Monday": "09:00-17:00", "Friday": "10:00-14:00"}
    
    consultation_type = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointments = relationship("Appointment", back_populates="doctor")
# =========================
# 5. APPOINTMENTS
# =========================
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(Integer, ForeignKey("clients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # NOTE: Changed Date/Time to String to prevent AI formatting errors
    appointment_date = Column(String(50)) 
    appointment_time = Column(String(50))
    
    status = Column(String(20), default="booked")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

# =========================
# 6. CALL LOGS
# =========================
class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), index=True)

    # VAPI Data
    caller_id = Column(Text, nullable=True)
    caller_number = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    
    # Content
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Medical Data
    symptoms_detected = Column(Text, nullable=True)
    appointment_intent = Column(Boolean, default=False)

    vapi_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="call_logs")