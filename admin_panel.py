from sqladmin import Admin, ModelView
import models

# ==========================================
# 0. ADMIN DASHBOARD SETUP
# ==========================================

class DoctorAdmin(ModelView, model=models.Doctor):
    column_list = [models.Doctor.id, models.Doctor.name, models.Doctor.specialization, models.Doctor.city]

class ClientAdmin(ModelView, model=models.Client):
    column_list = [models.Client.id, models.Client.name, models.Client.phone]

class AppointmentAdmin(ModelView, model=models.Appointment):
    column_list = [models.Appointment.id, models.Appointment.client_id, models.Appointment.doctor_id, models.Appointment.appointment_time, models.Appointment.status]

class CallLogAdmin(ModelView, model=models.CallLog):
    column_list = [models.CallLog.id, models.CallLog.caller_number, models.CallLog.summary]

def setup_admin(app, engine):
    admin = Admin(app, engine)
    admin.add_view(DoctorAdmin)
    admin.add_view(ClientAdmin)
    admin.add_view(AppointmentAdmin)
    admin.add_view(CallLogAdmin)
    return admin
