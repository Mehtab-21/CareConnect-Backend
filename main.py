from fastapi import FastAPI
from database import engine
import models
from admin_panel import setup_admin
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# CREATE APP (ONLY ONCE)
# ==========================================
app = FastAPI()

# ==========================================
# CORS
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# IMPORT ROUTERS
# ==========================================
from routes import doctors, appointments, call_logs, health

# ==========================================
# DATABASE
# ==========================================
models.Base.metadata.create_all(bind=engine)

# ==========================================
# ADMIN PANEL
# ==========================================
setup_admin(app, engine)

# ==========================================
# REGISTER ROUTERS
# ==========================================
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(call_logs.router)
app.include_router(health.router)
