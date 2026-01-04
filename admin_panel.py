from sqladmin import Admin, ModelView
import models

# ==========================================
# 0. ADMIN DASHBOARD SETUP
# ==========================================

class DoctorAdmin(ModelView, model=models.Doctor):
    name = "Doctor"
    name_plural = "Doctors"
    icon = "fa-solid fa-user-doctor"
    column_list = [
        models.Doctor.id, 
        models.Doctor.name, 
        models.Doctor.specialization, 
        models.Doctor.city,
        models.Doctor.hospital
    ]

class ClientAdmin(ModelView, model=models.Client):
    name = "Patient"
    name_plural = "Patients"
    icon = "fa-solid fa-user-injured"
    column_list = [
        models.Client.id, 
        models.Client.name, 
        models.Client.phone,
        models.Client.zipcode
    ]
    column_searchable_list = [models.Client.name, models.Client.phone]

class AppointmentAdmin(ModelView, model=models.Appointment):
    name = "Appointment"
    name_plural = "Appointments"
    icon = "fa-solid fa-calendar-check"
    column_list = [
        models.Appointment.id, 
        models.Appointment.client_id, 
        models.Appointment.doctor_id, 
        models.Appointment.appointment_date, 
        models.Appointment.appointment_time, 
        models.Appointment.status
    ]

class CallLogAdmin(ModelView, model=models.CallLog):
    name = "Triage Log"
    name_plural = "Triage Logs"
    icon = "fa-solid fa-file-medical"
    
    # --- FIXED COLUMNS (Matches your new Schema) ---
    column_list = [
        models.CallLog.id, 
        models.CallLog.client_id,    # Link to the patient
        models.CallLog.specialty,    # "Dermatology"
        models.CallLog.urgency_score,# 1-10
        models.CallLog.status,       # "NEW"
        models.CallLog.summary,      # "Patient reports..."
        models.CallLog.created_at
    ]
    
    # Detail view to see the long JSON data
    can_view_details = True
    column_details_list = [
        models.CallLog.id,
        models.CallLog.client,
        models.CallLog.summary,
        models.CallLog.symptoms,
        models.CallLog.patient_quotes,      # JSON data
        models.CallLog.extracted_keywords,  # JSON data
        models.CallLog.transcript
    ]

def setup_admin(app, engine):
    admin = Admin(app, engine)
    admin.add_view(DoctorAdmin)
    admin.add_view(ClientAdmin)
    admin.add_view(AppointmentAdmin)
    admin.add_view(CallLogAdmin)
    return admin