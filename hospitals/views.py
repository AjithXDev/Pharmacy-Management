from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from reception.models import Token
from accounts.models import *
from datetime import timedelta
from django.utils import timezone
import json
from django.db.models import Count
from django.db.models.functions import ExtractHour



@login_required
def hospital_dashboard(request):

    if request.user.role != "HOSPITAL_ADMIN":
        return redirect("accounts/login")

    hospital = request.user.hospital
    pharmacies = Pharmacy.objects.filter(hospital=hospital)

    # 🔹 Pharmacy counts
    total_pharmacy = pharmacies.count()
    active_pharmacy = pharmacies.filter(is_active=True).count()
    inactive_pharmacy = pharmacies.filter(is_active=False).count()

    today = timezone.now().date()

    # 🔥 TOTAL TOKENS TODAY (NEW FIX)
    tokens_today = Token.objects.filter(
        hospital=hospital,
        created_at__date=today
    )

    tokens_today_count = tokens_today.count()
    waiting_tokens = tokens_today.filter(status="WAITING").count()
    completed_tokens = tokens_today.filter(status="COMPLETED").count()

    # 🔹 Hourly token distribution (For chart only)
    hourly_data = (
        tokens_today
        .annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )

    hour_labels = [f"{entry['hour']}:00" for entry in hourly_data]
    hour_counts = [entry['count'] for entry in hourly_data]

    # 🔹 Pharmacy comparison (All time load)
    pharmacy_load = (
        Token.objects
        .filter(hospital=hospital)
        .values('pharmacy__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    pharmacy_labels = [entry['pharmacy__name'] for entry in pharmacy_load]
    pharmacy_counts = [entry['count'] for entry in pharmacy_load]

    context = {
        "hospital": hospital,
        "admin": request.user,
        "total_pharmacy": total_pharmacy,
        "active_pharmacy": active_pharmacy,
        "inactive_pharmacy": inactive_pharmacy,

        # 🔥 CORRECT TOKEN DATA
        "tokens_today_count": tokens_today_count,
        "waiting_tokens": waiting_tokens,
        "completed_tokens": completed_tokens,

        # 🔹 Chart Data
        "hour_labels": json.dumps(hour_labels),
        "hour_counts": json.dumps(hour_counts),
        "pharmacy_labels": json.dumps(pharmacy_labels),
        "pharmacy_counts": json.dumps(pharmacy_counts),
    }

    return render(request, "hospitals/dashboard.html", context)

@login_required
def hospital_kpi(request):

    if request.user.role != "HOSPITAL_ADMIN":
        return redirect("accounts:login")

    hospital = request.user.hospital
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    today_qs = Token.objects.filter(
        hospital=hospital,
        created_at__date=today
    )

    yesterday_qs = Token.objects.filter(
        hospital=hospital,
        created_at__date=yesterday
    )

    tokens_today = today_qs.count()
    tokens_yesterday = yesterday_qs.count()

    waiting = today_qs.filter(status="WAITING").count()
    completed = today_qs.filter(status="COMPLETED").count()

    trend = tokens_today - tokens_yesterday
    trend_abs = abs(trend)

    # 🔥 Chart Data
    chart_labels = json.dumps(["Yesterday", "Today"])
    chart_data = json.dumps([tokens_yesterday, tokens_today])

    context = {
        "tokens_today": tokens_today,
        "waiting": waiting,
        "completed": completed,
        "trend": trend,
        "trend_abs": trend_abs,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }

    return render(request, "hospitals/kpi.html", context)

from django.db.models.functions import TruncDate

@login_required
def hospital_analytics(request):

    if request.user.role != "HOSPITAL_ADMIN":
        return redirect("accounts/login")

    hospital = request.user.hospital
    today = timezone.now().date()

    # 🔷 Last 7 Days Daily Trend
    daily_labels = []
    daily_counts = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Token.objects.filter(
            hospital=hospital,
            created_at__date=day
        ).count()

        daily_labels.append(day.strftime("%d %b"))
        daily_counts.append(count)

    # 🔷 Hourly Distribution (Today)
    hour_labels = []
    hour_counts = []

    for h in range(24):
        count = Token.objects.filter(
            hospital=hospital,
            created_at__date=today,
            created_at__hour=h
        ).count()

        hour_labels.append(f"{h}:00")
        hour_counts.append(count)

    # 🔷 Pharmacy Comparison
    pharmacy_data = (
        Token.objects
        .filter(hospital=hospital)
        .values("pharmacy__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    pharmacy_labels = [p["pharmacy__name"] for p in pharmacy_data]
    pharmacy_counts = [p["count"] for p in pharmacy_data]

    context = {
        "daily_labels": json.dumps(daily_labels),
        "daily_counts": json.dumps(daily_counts),
        "hour_labels": json.dumps(hour_labels),
        "hour_counts": json.dumps(hour_counts),
        "pharmacy_labels": json.dumps(pharmacy_labels),
        "pharmacy_counts": json.dumps(pharmacy_counts),
    }

    return render(request, "hospitals/analytics.html", context)

@login_required
def pharmacy_overview(request):

    if request.user.role != "HOSPITAL_ADMIN":
        return redirect("accounts/login")

    hospital = request.user.hospital
    today = timezone.now().date()

    pharmacies = Pharmacy.objects.filter(hospital=hospital)

    pharmacy_data = []

    for p in pharmacies:
        tokens_today = Token.objects.filter(
            pharmacy=p,
            created_at__date=today
        ).count()

        pharmacy_data.append({
            "id": p.id,
            "name": p.name,
            "floor": p.floor_name,
            "type": p.get_pharmacy_type_display(),
            "is_active": getattr(p, "is_active", True),  # safe check
            "tokens_today": tokens_today
        })

    return render(request, "hospitals/pharmacy_overview.html", {
        "pharmacies": pharmacy_data
    })

@login_required
def toggle_pharmacy(request, pk):

    pharmacy = get_object_or_404(Pharmacy, id=pk)

    pharmacy.is_active = not pharmacy.is_active
    pharmacy.save()

    if not pharmacy.is_active:
        Counter.objects.filter(
            pharmacy=pharmacy
        ).update(is_active=False)

    return redirect("pharmacy_overview")




@login_required
def counter_list(request, pharmacy_id):

    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)

    # Security: Only same hospital admin
    if request.user.hospital != pharmacy.hospital:
        return redirect("hospital_dashboard")

    counters = pharmacy.counters.all()

    return render(request, "hospitals/counter_list.html", {
        "pharmacy": pharmacy,
        "counters": counters
    })


@login_required
def add_counter(request, pharmacy_id):

    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)

    if request.user.hospital != pharmacy.hospital:
        return redirect("hospital_dashboard")

    if request.method == "POST":
        counter_number = request.POST.get("counter_number")

        Counter.objects.create(
            pharmacy=pharmacy,
            counter_number=counter_number
        )

        return redirect("counter_list", pharmacy_id=pharmacy.id)

    return render(request, "hospitals/add_counter.html", {
        "pharmacy": pharmacy
    })
@login_required
def add_pharmacy(request):

    if request.user.role != 'HOSPITAL_ADMIN':
        return redirect('login')

    hospital = request.user.hospital

    if request.method == 'POST':
        name = request.POST.get('name')
        floor = request.POST.get('floor')
        pharmacy_type = request.POST.get('pharmacy_type')

        Pharmacy.objects.create(
            hospital=hospital,
            name=name,
            floor_name=floor,
            pharmacy_type=pharmacy_type
        )

        return redirect('hospital_dashboard')

    return render(request, 'hospitals/add_pharmacy.html')


@login_required
def toggle_counter(request, counter_id):

    counter = get_object_or_404(Counter, id=counter_id)

    counter.is_active = not counter.is_active
    counter.save()

    return redirect("counter_list", pharmacy_id=counter.pharmacy.id)



@login_required
def assign_pharmacy_head(request, pharmacy_id):

    pharmacy = get_object_or_404(
        Pharmacy,
        id=pharmacy_id,
        hospital=request.user.hospital
    )

    # Users in same hospital but not already assigned
    available_users = User.objects.filter(
        hospital=request.user.hospital,
        pharmacy__isnull=True
    ).exclude(role="PLATFORM_ADMIN")

    

    if request.method == "POST":
        user_id = request.POST.get("user_id")

        user = get_object_or_404(
            User,
            id=user_id,
            hospital=request.user.hospital
        )

        user.pharmacy = pharmacy
        user.role = "PHARMACY_MANAGER"
        user.save()
        existing_head = User.objects.filter(
        pharmacy=pharmacy,
        role="PHARMACY_MANAGER"
).exists()

        if existing_head:
            messages.error(request, "This pharmacy already has a head.")
            return redirect("hospitals/pharmacy_overview")

        return redirect("hospitals/pharmacy_overview")

    return render(
        request,
        "hospitals/assign_head.html",
        {
            "pharmacy": pharmacy,
            "users": available_users
        }
    )
@login_required
def create_pharmacy_head(request, pharmacy_id):

    pharmacy = get_object_or_404(
        Pharmacy,
        id=pharmacy_id,
        hospital=request.user.hospital
    )

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request,
                          "hospitals/assign_head.html",
                          {
                              "pharmacy": pharmacy,
                              "error": "Username already exists"
                          })

        # 🔥 IMPORTANT PART
        user = User.objects.create_user(
            username=username,
            password=password
        )

        user.hospital = request.user.hospital
        user.pharmacy = pharmacy
        user.role = "PHARMACY_MANAGER"
        user.save()

        return redirect("pharmacy_heads")

    return render(
        request,
        "hospitals/assign_head.html",
        {"pharmacy": pharmacy}
    )
@login_required
def remove_pharmacy_head(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id,
        hospital=request.user.hospital,
        role="PHARMACY_MANAGER"
    )

    # 🔥 Remove pharmacy assignment
    user.pharmacy = None
    user.role = "HOSPITAL_ADMIN"   # or normal staff role
    user.save()

    return redirect("pharmacy_heads")

@login_required
def all_counters(request):

    hospital = request.user.hospital

    counters = Counter.objects.filter(
        pharmacy__hospital=hospital
    ).select_related("pharmacy")

    return render(request, "hospitals/all_counters.html", {
        "counters": counters
    })

@login_required
def pharmacy_heads(request):

    heads = User.objects.filter(
        hospital=request.user.hospital,
        role="PHARMACY_MANAGER"
    )

    return render(
        request,
        "hospitals/pharmacy_heads.html",
        {"heads": heads}
    )


@login_required
def edit_pharmacy(request, pk):

    pharmacy = get_object_or_404(Pharmacy, id=pk)

    # Security: only same hospital
    if request.user.hospital != pharmacy.hospital:
        return redirect("hospitals/pharmacy_overview")

    if request.method == "POST":
        pharmacy.name = request.POST.get("name")
        pharmacy.floor_name = request.POST.get("floor_name")
        pharmacy.pharmacy_type = request.POST.get("pharmacy_type")
        pharmacy.save()

        return redirect("pharmacy_overview")

    return render(request,
                  "hospitals/edit_pharmacy.html",
                  {"pharmacy": pharmacy})

@login_required
def delete_pharmacy(request, pk):

    pharmacy = get_object_or_404(
        Pharmacy,
        id=pk,
        hospital=request.user.hospital
    )

    # 🔥 Delete counters
    Counter.objects.filter(pharmacy=pharmacy).delete()

    # 🔥 Delete pharmacy head users
    User.objects.filter(
        pharmacy=pharmacy,
        role="PHARMACY_MANAGER"
    ).delete()

    pharmacy.delete()

    return redirect("pharmacy_overview")

@login_required
def edit_counter(request, pk):

    counter = get_object_or_404(Counter, id=pk)

    # security
    if request.user.hospital != counter.pharmacy.hospital:
        return redirect("hospitals/pharmacy_overview")

    if request.method == "POST":
        counter.counter_number = request.POST.get("counter_number")
        counter.save()
        return redirect("all_counters")

    return render(request,
                  "hospitals/edit_counter.html",
                  {"counter": counter})

@login_required
def delete_counter(request, pk):

    counter = get_object_or_404(Counter, id=pk)

    if request.user.hospital != counter.pharmacy.hospital:
        return redirect("hospitals/pharmacy_overview")

    if request.method == "POST":
        counter.delete()
        return redirect("all_counters")
    return render(request,
                  "hospitals/delete_counter.html",
                  {"counter": counter})



@login_required
def create_reception_staff(request):

    if request.user.role != "HOSPITAL_ADMIN":
        return redirect("login")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, "hospitals/create_reception.html", {
                "error": "Username already exists"
            })

        User.objects.create_user(
            username=username,
            password=password,
            role="RECEPTION_STAFF",
            hospital=request.user.hospital
        )

        return redirect("hospital_dashboard")

    return render(request, "hospitals/create_reception.html")


def add_pharmacist(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        pharmacy_id = request.POST.get("pharmacy")

        pharmacy = Pharmacy.objects.get(id=pharmacy_id)

        User.objects.create_user(

            username=username,
            password=password,
            role="PHARMACIST",
            hospital=request.user.hospital,
            pharmacy=pharmacy
        )

        messages.success(request, "Pharmacist created successfully")

        return redirect("hospital_dashboard")

    pharmacies = Pharmacy.objects.filter(
        hospital=request.user.hospital
    )

    return render(
        request,
        "hospitals/add_pharmacist.html",
        {"pharmacies": pharmacies}
    )