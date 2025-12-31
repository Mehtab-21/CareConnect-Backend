from database import SessionLocal, engine
import models
import json

# Drop everything and recreate (Fresh Start)
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("🌱 Seeding Database...")

# 1. Create Doctors
doctors = [
    models.Doctor(
        name="Gregory House",
        specialization="Diagnostic Medicine",
        hospital="Princeton-Plainsboro",
        city="Princeton",
        zipcode="08540",
        languages=["English", "Spanish"],
        insurance=["Blue Cross", "Aetna"]
    ),
    models.Doctor(
        name="Stephen Strange",
        specialization="Neurosurgeon",
        hospital="Metro General",
        city="New York",
        zipcode="10001",
        languages=["English"],
        insurance=["Aetna", "UnitedHealth"]
    ),
    models.Doctor(
        name="Meredith Grey",
        specialization="General Surgeon",
        hospital="Seattle Grace",
        city="Seattle",
        zipcode="98101",
        languages=["English"],
        insurance=["Blue Cross"]
    )
]

db.add_all(doctors)
db.commit()

print("✅ Added 3 Doctors.")
print("🚀 Database is ready!")
db.close()