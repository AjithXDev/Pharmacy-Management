from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.reception_dashboard, name="reception_dashboard"),
    path("add-patient/", views.add_patient, name="add_patient"),
    path("patient/<int:patient_id>/", views.patient_card, name="patient_card"),
path("generate-token/<int:prescription_id>/<int:pharmacy_id>/",
     views.generate_token,
     name="generate_token"),    path("success/<int:token_id>/", views.token_success, name="token_success"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/export/", views.export_patients, name="export_patients"),
    path("patients/edit/<int:patient_id>/", views.edit_patient, name="edit_patient"),
path("patients/delete/<int:patient_id>/", views.delete_patient, name="delete_patient"),
path("prescription/create/<int:patient_id>/",
     views.create_prescription,
     name="create_prescription"),
# 🔥 For prescription medicines (IMPORTANT)
path("prescription/<int:prescription_id>/medicines/",
     views.add_medicines,
     name="add_medicines"),



]