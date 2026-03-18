from django.shortcuts import render, redirect
from django.utils import timezone
from pharmacy.models  import *
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect



def pharmacist_dashboard(request):

    waiting = Preparation.objects.filter(status="PENDING").count()

    preparing = Preparation.objects.filter(
        status="PREPARING"
    ).select_related("token", "token__patient")

    dispatched = Preparation.objects.filter(status="DISPATCHED").count()

    recent_dispatch = Preparation.objects.filter(
        status="DISPATCHED"
    ).order_by("-end_time")[:5]

    context = {
        "waiting": waiting,
        "preparing": preparing,
        "dispatched": dispatched,
        "recent_dispatch": recent_dispatch,
    }

    return render(request, "pharmacist/dashboard.html", context)


def start_preparing(request, token_id):

    prep = Preparation.objects.get(token__id=token_id)

    prep.status = "PREPARING"
    prep.start_time = timezone.now()

    prep.save()

    return redirect("pharmacist_dashboard")


def dispatch_medicine(request, token_id):

    prep = Preparation.objects.get(token__id=token_id)

    prep.status = "DISPATCHED"
    prep.end_time = timezone.now()

    if prep.start_time:
        prep.actual_prepare_time = (
            prep.end_time - prep.start_time
        ).total_seconds() / 60

    prep.save()

    return redirect("pharmacist_dashboard")

def pharmacist_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            return redirect("pharmacist_dashboard")

    return render(request, "pharmacist/login.html")