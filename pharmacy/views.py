from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from hospitals.models import *
from reception.models import *
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum

from reception.models import Token, PrescriptionItem
from reception.ml_predict import predict_billing_time


# 🔹 Dashboard
@login_required
def pharmacy_dashboard(request):

    pharmacy = request.user.pharmacy

    total_counters = Counter.objects.filter(pharmacy=pharmacy).count()
    active_counters = Counter.objects.filter(pharmacy=pharmacy, is_active=True).count()
    waiting_count = Token.objects.filter(pharmacy=pharmacy, status="WAITING").count()

    # 4 min alert
    alerts = []
    max_time = timedelta(minutes=4)

    billed_tokens = Token.objects.filter(
        pharmacy=pharmacy,
        status="BILLED",
        billing_start_time__isnull=False
    )

    auto_complete_billing()

    return render(request, "pharmacy/dashboard.html", {
        "pharmacy": pharmacy,
        "total_counters": total_counters,
        "active_counters": active_counters,
        "waiting_count": waiting_count,
        "alerts": alerts
    })


# 🔹 Counter List
@login_required
def counter_list(request):

    pharmacy = request.user.pharmacy
    counters = Counter.objects.filter(pharmacy=pharmacy)

    counter_data = []

    for counter in counters:
        current_token = Token.objects.filter(
            pharmacy=pharmacy,
            counter=counter,
            status="BILLED"
        ).first()

        counter_data.append({
            "counter": counter,
            "token": current_token
        })

    return render(request, "pharmacy/counter_list.html", {
        "counter_data": counter_data
    })

@login_required
def start_billing(request, token_id):

    token = Token.objects.get(id=token_id)

    token.billing_start_time = timezone.now()
    token.status = "BILLED"

    # 🔥 calculate medicine count
    medicine_count = PrescriptionItem.objects.filter(
        prescription=token.prescription
    ).count()

    # predicted time (seconds)
    predicted_time = predict_billing_time(
        medicine_count,
        0,
        0,
        1,
        0,
        0
    )

    # 🔥 set expected billing finish
    token.billing_expected_time = (
        token.billing_start_time + timedelta(seconds=predicted_time)
    )

    token.save()

    return redirect("counter_list")

def auto_complete_billing():

    now = timezone.now()

    tokens = Token.objects.filter(
        status="BILLING",
        billing_expected_time__lte=now
    )

    for token in tokens:
        token.status = "COMPLETED"
        token.billing_completed_time = token.billing_expected_time  # 🔥 never exceed
        token.save()


# 🔹 Add Counter
@login_required
def add_counter(request):

    pharmacy = request.user.pharmacy

    if request.method == "POST":
        number = request.POST.get("counter_number")

        Counter.objects.create(
            pharmacy=pharmacy,
            counter_number=number
        )

        return redirect("counter_list")

    return render(request, "pharmacy/add_counter.html")


# 🔹 Waiting Page
@login_required
def waiting_list(request):

    pharmacy = request.user.pharmacy
    service_time = timedelta(minutes=4)

    active_counters = Counter.objects.filter(
        pharmacy=pharmacy,
        is_active=True
    )

    waiting_tokens = list(Token.objects.filter(
        pharmacy=pharmacy,
        status="WAITING"
    ).order_by("token_number"))

    if active_counters.exists():

        running_tokens = Token.objects.filter(
            pharmacy=pharmacy,
            status="BILLED"
        )

        base_time = timezone.now()

        if running_tokens.exists():
            latest_finish = max([
                token.billing_start_time + service_time
                for token in running_tokens
                if token.billing_start_time
            ])
            base_time = latest_finish

        for index, token in enumerate(waiting_tokens):
            token.expected_time = base_time + (service_time * index)

    return render(request, "pharmacy/waiting_list.html", {
        "waiting_tokens": waiting_tokens
    })
# 🔹 Complete Billing
@login_required
def complete_billing(request, token_id):

    token = get_object_or_404(Token, id=token_id)
    counter = token.counter

    token.status = "COMPLETED"
    token.counter = None
    token.save()

    if counter:
        counter.is_busy = False
        counter.save()
    
    recalculate_queue(token.pharmacy)

    return redirect("counter_list")


# 🔹 Toggle Counter
@login_required
def toggle_counter(request, counter_id):

    counter = get_object_or_404(Counter, id=counter_id)
    counter.is_active = not counter.is_active
    counter.save()
    
    recalculate_queue(counter.pharmacy)

    return redirect("counter_list")




def recalculate_queue(pharmacy):

    active_counters = Counter.objects.filter(
        pharmacy=pharmacy,
        is_active=True
    )

    if not active_counters.exists():
        return

    # waiting tokens
    waiting_tokens = Token.objects.filter(
        pharmacy=pharmacy,
        status="WAITING"
    ).order_by("token_number")   # better than created_at

    for counter in active_counters:

        # check if counter already busy
        current = Token.objects.filter(
            pharmacy=pharmacy,
            counter=counter,
            status="BILLED"
        ).first()

        if current:
            continue

        # next token
        next_token = waiting_tokens.first()

        if not next_token:
            break

        # 🔥 billing start
        next_token.status = "BILLED"
        next_token.counter = counter
        next_token.billing_start_time = timezone.now()

        # 🔥 medicine count
        medicine_count = PrescriptionItem.objects.filter(
            prescription=next_token.prescription
        ).count()

        # 🔥 ML predicted billing time
        predicted = predict_billing_time(
            medicine_count,
            0,   # test_count
            0,   # tokens_before
            1,   # active_counters
            0,   # payment_type
            0    # emergency
        )

        # 🔥 expected finish time
        next_token.billing_expected_time = (
            next_token.billing_start_time +
            timedelta(seconds=predicted*3)
        )

        next_token.save()

        waiting_tokens = waiting_tokens.exclude(id=next_token.id)


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from reception.models import Token
from .models import Preparation


def prepare_list(request):

    tokens = Token.objects.filter(status="COMPLETED")  # billing finished

    for token in tokens:
        Preparation.objects.get_or_create(token=token)

    preparations = Preparation.objects.all()

    return render(request, "pharmacy/prepare_list.html", {
        "preparations": preparations
    })

def start_prepare(request, prep_id):

    prep = get_object_or_404(Preparation, id=prep_id)

    if not prep.token.prescription:
        return redirect("prepare_list")

    prescription = prep.token.prescription

    # 🔥 calculate total quantity
    medicine_count = prescription.items.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    prep.medicine_count = medicine_count

    prep.start_time = timezone.now()

    per_medicine_seconds = 40  # change later if needed

    total_seconds = medicine_count * per_medicine_seconds

    prep.expected_dispatch_time = (
        prep.start_time + timedelta(seconds=total_seconds)
    )

    prep.status = "PREPARING"
    prep.save()

    return redirect("prepare_list")
def finish_prepare(request, prep_id):

    prep = get_object_or_404(Preparation, id=prep_id)

    prep.status = "DISPATCHED"
    prep.end_time = timezone.now()

    if prep.start_time:
        prep.actual_prepare_time = (
            prep.end_time - prep.start_time
        ).total_seconds() / 60

    prep.save()

    return redirect("prepare_list")

from reception.queue_engine import update_future_tokens
from datetime import timedelta


def delay_billing(request, token_id):

    token = Token.objects.get(id=token_id)

    delay_seconds = 120

    token.billing_expected_time += timedelta(seconds=delay_seconds)
    token.save()

    update_future_tokens(
        pharmacy=token.pharmacy,
        delayed_token=token,
        delay_seconds=delay_seconds
    )

    return redirect("pharmacy_dashboard")