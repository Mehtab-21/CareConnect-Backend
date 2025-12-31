from fastapi import FastAPI
from database import engine
import models
from admin_panel import setup_admin

# Import Routers
from routes import doctors, appointments, call_logs, health

# Create Tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ==========================================
# 0. ADMIN DASHBOARD SETUP
# ==========================================
setup_admin(app, engine)

# ==========================================
# REGISTER ROUTERS
# ==========================================
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(call_logs.router)
app.include_router(health.router)