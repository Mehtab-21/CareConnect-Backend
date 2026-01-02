from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from sqlalchemy import text  # <--- Import this

def reset_database():
    db = SessionLocal()
    print("\n🗑️  CLEARING OLD DATA & RESETTING IDs...")
    
    try:
        # TRUNCATE removes all data and RESTART IDENTITY resets IDs to 1
        # CASCADE ensures child tables (like appointments) are cleared too
        db.execute(text("TRUNCATE TABLE appointments, call_logs, doctors, clients, users, roles RESTART IDENTITY CASCADE;"))
        db.commit()
        print("✅ Tables truncated and IDs reset to 1.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return
    finally:
        db.close()
# --- 2. INSERT NEW DATA ---
def seed_data():
    db = SessionLocal()
    print("\n🌱 SEEDING NEW DATA...")

    # --- DOCTORS (All set to HYBRID) ---
    doctors = [
        models.Doctor(
            name="Dr. Emily Carter",
            specialization="Cardiologist",
            hospital="NY Presbyterian",
            city="New York",
            zipcode="10001",
            languages=["English", "Spanish"],
            insurance=["BlueCross", "Aetna", "Medicare"],
            consultation_type="Hybrid",  # <--- UPDATED
            availability={
                "Monday": "09:00-17:00",
                "Wednesday": "09:00-17:00",
                "Friday": "09:00-13:00"
            }
        ),
        models.Doctor(
            name="Dr. Marcus Hayes",
            specialization="Dermatologist",
            hospital="Cedars-Sinai",
            city="Beverly Hills",
            zipcode="90210",
            languages=["English"],
            insurance=["Cigna", "UnitedHealth"],
            consultation_type="Hybrid",  # <--- UPDATED
            availability={
                "Tuesday": "10:00-18:00",
                "Thursday": "10:00-18:00"
            }
        ),
        models.Doctor(
            name="Dr. Sarah Lee",
            specialization="Pediatrician",
            hospital="Chicago Children's",
            city="Chicago",
            zipcode="60614",
            languages=["English", "Korean"],
            insurance=["BlueCross", "Medicaid"],
            consultation_type="Hybrid",  # <--- UPDATED
            availability={
                "Monday": "08:00-16:00",
                "Tuesday": "08:00-16:00",
                "Wednesday": "08:00-16:00",
                "Thursday": "08:00-16:00",
                "Friday": "08:00-16:00"
            }
        ),
        models.Doctor(
            name="Dr. James Wilson",
            specialization="General Physician",
            hospital="Texas Health",
            city="Dallas",
            zipcode="75001",
            languages=["English"],
            insurance=["Aetna", "Humana", "Medicare"],
            consultation_type="Hybrid",  # <--- UPDATED
            availability={
                "Saturday": "09:00-13:00",
                "Sunday": "09:00-13:00"
            }
        ),
        models.Doctor(
            name="Dr. Sofia Rodriguez",
            specialization="Neurologist",
            hospital="Miami General",
            city="Miami",
            zipcode="33101",
            languages=["English", "Spanish", "Portuguese"],
            insurance=["BlueCross", "UnitedHealth"],
            consultation_type="Hybrid",  # <--- UPDATED
            availability={
                "Monday": "13:00-19:00",
                "Wednesday": "13:00-19:00"
            }
        )
    ]

    db.add_all(doctors)
    db.commit()
    print(f"   - Added {len(doctors)} Doctors (All Hybrid).")

    # --- CLIENTS ---
    clients = [
        models.Client(name="John Doe", phone="555-0101", email="john.doe@example.com", zipcode="10001"),
        models.Client(name="Maria Garcia", phone="555-0102", email="maria.g@example.com", zipcode="90210"),
        models.Client(name="Robert Smith", phone="555-0103", email="r.smith@test.com", zipcode="60614")
    ]

    db.add_all(clients)
    db.commit()
    print(f"   - Added {len(clients)} Clients.")

    # --- INITIAL APPOINTMENTS ---
    # Refresh to get IDs
    for doc in doctors: db.refresh(doc)
    for cli in clients: db.refresh(cli)

    appointments = [
        models.Appointment(
            client_id=clients[0].id,
            doctor_id=doctors[0].id,
            appointment_date="2025-11-15",
            appointment_time="10:00",
            status="confirmed"
        ),
        models.Appointment(
            client_id=clients[1].id,
            doctor_id=doctors[1].id,
            appointment_date="2025-11-16",
            appointment_time="14:30",
            status="completed"
        )
    ]

    db.add_all(appointments)
    db.commit()
    print(f"   - Added {len(appointments)} Initial Appointments.")
    
    db.close()
    print("\n✨ DATABASE RESET COMPLETE! ✨")

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=engine)
    reset_database()
    seed_data()