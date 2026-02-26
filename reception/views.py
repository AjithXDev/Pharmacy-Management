from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from hospitals.models import *
from .models import *
import csv
from django.http import HttpResponse
from django.db.models import Avg
from django.utils import timezone
from datetime import date
from datetime import timedelta
import math
from pharmacy.views import *




@login_required
def generate_token(request, prescription_id, pharmacy_id):

    if request.user.role != "RECEPTION_STAFF":
        return redirect("login")

    if request.method != "POST":
        return redirect("reception_dashboard")

    prescription = get_object_or_404(
        Prescription,
        id=prescription_id
    )

    patient = prescription.patient

    pharmacy = get_object_or_404(
        Pharmacy,
        id=pharmacy_id,
        hospital=request.user.hospital
    )

    # 🔹 Next token number
    last_token = Token.objects.filter(
        pharmacy=pharmacy
    ).aggregate(Max('token_number'))

    next_number = 1
    if last_token['token_number__max']:
        next_number = last_token['token_number__max'] + 1

    # 🔹 Count waiting tokens before this one
    waiting_count = Token.objects.filter(
        pharmacy=pharmacy,
        status="WAITING"
    ).count()

    # 🔹 Assume 5 mins per patient (you can change this)
    average_minutes_per_patient = 5

    expected_wait = waiting_count * average_minutes_per_patient

    token = Token.objects.create(
        hospital=pharmacy.hospital,
        pharmacy=pharmacy,
        patient=patient,
        prescription=prescription,
        token_number=next_number,
        status="WAITING"
    )

    recalculate_queue(pharmacy)

    # 🔥 Pass expected time through URL (temporary store)
    request.session["expected_wait"] = expected_wait

    return redirect("token_success", token_id=token.id)
    
@login_required
def reception_dashboard(request):

    if request.user.role != "RECEPTION_STAFF":
        return redirect("login")

    today = date.today()

    # 🔹 Patients Registered Today
    patients_today = Patient.objects.filter(
        hospital=request.user.hospital,
        created_at__date=today
    ).count()

    # 🔹 Active Tokens (Waiting Only)
    active_tokens = Token.objects.filter(
        hospital=request.user.hospital,
        status="WAITING"
    ).count()

    # 🔹 Average Waiting Time (minutes)
    tokens = Token.objects.filter(
        hospital=request.user.hospital,
        status="WAITING"
    )

    avg_wait = 0

    if tokens.exists():
        total_minutes = 0
        for token in tokens:
            diff = timezone.now() - token.created_at
            total_minutes += diff.total_seconds() / 60

        avg_wait = round(total_minutes / tokens.count())

    return render(request, "reception/dashboard.html", {
        "patients_today": patients_today,
        "active_tokens": active_tokens,
        "avg_wait": avg_wait
    })


    
@login_required
def token_success(request, token_id):

    token = get_object_or_404(Token, id=token_id)

    pharmacy = token.pharmacy

    # 🔥 Count waiting tokens created before this one
    waiting_count = Token.objects.filter(
        pharmacy=pharmacy,
        status="WAITING",
        created_at__lt=token.created_at
    ).count()

    # 🔹 Average time per patient
    average_minutes_per_patient = 5

    expected_wait = waiting_count * average_minutes_per_patient

    estimated_billing_time = timezone.now() + timedelta(minutes=expected_wait)

    context = {
        "token": token,
        "expected_wait_minutes": expected_wait,
        "estimated_billing_time": estimated_billing_time
    }

    return render(request, "reception/token_success.html", context)

@login_required
def add_patient(request):

    if request.user.role != "RECEPTION_STAFF":
        return redirect("login")

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        # 🔥 Reuse patient if phone exists
        patient, created = Patient.objects.get_or_create(
            hospital=request.user.hospital,
            phone=phone,
            defaults={
                "name": name,
                "age": age,
                "gender": gender
            }
        )

        return redirect("patient_card", patient_id=patient.id)

    return render(request, "reception/patient_form.html")

@login_required
def patient_card(request, patient_id):

    patient = get_object_or_404(
        Patient,
        id=patient_id,
        hospital=request.user.hospital
    )

    pharmacies = Pharmacy.objects.filter(
        hospital=request.user.hospital
    )
    print("Reception hospital:", request.user.hospital)
    print("Pharmacies:", pharmacies)

    return render(request, "reception/patient_card.html", {
        "patient": patient,
        "pharmacies": pharmacies
    })

@login_required
def patient_list(request):

    if request.user.role not in ["RECEPTION_STAFF", "HOSPITAL_ADMIN"]:
        return redirect("login")

    patients = Patient.objects.filter(
        hospital=request.user.hospital
    ).order_by("-created_at")

    return render(request, "reception/patient_list.html", {
        "patients": patients
    })

@login_required
def export_patients(request):

    if request.user.role not in ["RECEPTION_STAFF", "HOSPITAL_ADMIN"]:
        return redirect("login")

    patients = Patient.objects.filter(
        hospital=request.user.hospital
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patients.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Name",
        "Phone",
        "Age",
        "Gender",
        "Registered At"
    ])

    for p in patients:
        writer.writerow([
            p.name,
            p.phone,
            p.age,
            p.gender,
            p.created_at.strftime("%d-%m-%Y %H:%M")
        ])

    return response

@login_required
def edit_patient(request, patient_id):

    if request.user.role not in ["RECEPTION_STAFF", "HOSPITAL_ADMIN"]:
        return redirect("login")

    patient = get_object_or_404(
        Patient,
        id=patient_id,
        hospital=request.user.hospital
    )

    if request.method == "POST":
        patient.name = request.POST.get("name")
        patient.phone = request.POST.get("phone")
        patient.age = request.POST.get("age")
        patient.gender = request.POST.get("gender")
        patient.save()

        return redirect("patient_list")

    return render(request, "reception/edit_patient.html", {
        "patient": patient
    })

@login_required
def delete_patient(request, patient_id):

    if request.user.role not in ["RECEPTION_STAFF", "HOSPITAL_ADMIN"]:
        return redirect("login")

    patient = get_object_or_404(
        Patient,
        id=patient_id,
        hospital=request.user.hospital
    )

    if request.method == "POST":
        patient.delete()
        return redirect("patient_list")

    return render(request, "reception/delete_patient.html", {
        "patient": patient
    })

@login_required
def create_prescription(request, patient_id):

    patient = get_object_or_404(
        Patient,
        id=patient_id,
        hospital=request.user.hospital
    )

    prescription = Prescription.objects.create(
        patient=patient
    )

    return redirect("add_medicines", prescription_id=prescription.id)

from pharmacy.models import Medicine

@login_required
def medicine_list(request):

    if request.user.role != "RECEPTION_STAFF":
        return redirect("login")

    medicines = Medicine.objects.all()

    return render(request, "reception/medicine_list.html", {
        "medicines": medicines
    })

@login_required
def add_medicines(request, prescription_id):

    prescription = get_object_or_404(
        Prescription,
        id=prescription_id
    )

    pharmacies = Pharmacy.objects.filter(
        hospital=request.user.hospital
    )

    if request.method == "POST":

        name = request.POST.get("name")
        med_type = request.POST.get("type")
        cold_storage = request.POST.get("cold_storage") == "on"
        quantity = request.POST.get("quantity")

        if name and quantity:

            # 🔥 Check if medicine already exists
            medicine, created = Medicine.objects.get_or_create(
                name=name,
                defaults={
                    "type": med_type,
                    "cold_storage": cold_storage
                }
            )

            # 🔥 Add to prescription
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine=medicine,
                quantity=int(quantity)
            )

        return redirect("add_medicines", prescription_id=prescription.id)

    items = prescription.items.all()

    return render(request, "reception/add_medicines.html", {
        "prescription": prescription,
        "items": items,
        "pharmacies": pharmacies
    })