from django.shortcuts import render, redirect

from hospitals.models import Hospital
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils import timezone
import json
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.db.models import Q
import csv
from django.http import HttpResponse
from .models import *
from accounts.models import *



@login_required
def platform_dashboard(request):
    hospitals = Hospital.objects.all()
    hospital_count = hospitals.count()

    now = timezone.now()

    # New clients this month
    new_clients_this_month = hospitals.filter(
        created_at__month=now.month,
        created_at__year=now.year
    ).count()

    # Previous month growth
    last_month = now - timedelta(days=30)
    previous_month_count = hospitals.filter(
        created_at__month=last_month.month,
        created_at__year=last_month.year
    ).count()

    growth_percentage = 0
    if previous_month_count > 0:
        growth_percentage = (
            (new_clients_this_month - previous_month_count)
            / previous_month_count
        ) * 100

    # --- 6 Month Trend Data ---
    six_months_ago = now - timedelta(days=180)

    monthly_data = (
        hospitals
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    trend_labels = []
    trend_counts = []

    for entry in monthly_data:
        trend_labels.append(entry['month'].strftime("%b"))
        trend_counts.append(entry['count'])

    # --- Location Distribution ---
    location_data = (
        hospitals
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    location_labels = []
    location_counts = []

    for entry in location_data:
        location_labels.append(entry['location'] if entry['location'] else "Unknown")
        location_counts.append(entry['count'])

    context = {
        'hospital_count': hospital_count,
        'new_clients_this_month': new_clients_this_month,
        'growth_percentage': growth_percentage,
        'trend_labels': json.dumps(trend_labels),
        'trend_counts': json.dumps(trend_counts),
        'location_labels': json.dumps(location_labels),
        'location_counts': json.dumps(location_counts),
    }

    return render(request, 'platform/platform_dashboard.html', context)

@login_required
def clients_page(request):
    print("USERNAME:", request.user.username)
    print("ROLE:", request.user.role)
    print("IS SUPERUSER:", request.user.is_superuser)

    search_query = request.GET.get('search', '')

    hospitals = Hospital.objects.all()

    if search_query:
        hospitals = hospitals.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    hospital_data = []

    for hospital in hospitals:
        admin = User.objects.filter(
            role='HOSPITAL_ADMIN',
            hospital=hospital
        ).first()

        hospital_data.append({
            'hospital': hospital,
            'admin_username': admin.username if admin else "No Admin"
        })

    return render(request, 'platform/clients.html', {
        'hospital_data': hospital_data,
        'search_query': search_query
    })

@login_required
def admins_page(request):
    hospital_admins = User.objects.filter(role='HOSPITAL_ADMIN')
    return render(request, 'platform/admin.html', {
        'hospital_admins': hospital_admins
    })

@login_required
def export_hospitals(request):

    if not (request.user.is_superuser or request.user.role == 'PLATFORM_ADMIN'):
        return redirect('login')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hospitals.csv"'

    writer = csv.writer(response)
    writer.writerow(['Hospital Name', 'Location', 'Admin Username'])

    hospitals = Hospital.objects.all()

    for hospital in hospitals:
        admin = User.objects.filter(
            role='HOSPITAL_ADMIN',
            hospital=hospital
        ).first()

        writer.writerow([
            hospital.name,
            hospital.location,
            admin.username if admin else "No Admin"
        ])

    return response

@login_required
def export_admins(request):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hospital_admins.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Hospital', 'Last Login'])

    admins = User.objects.filter(role='HOSPITAL_ADMIN')

    for admin in admins:
        writer.writerow([
            admin.username,
            admin.hospital.name if admin.hospital else "N/A",
            admin.last_login if admin.last_login else "Never Logged In"
        ])

    return response


@login_required
def audit_logs_page(request):

    logs = AuditLog.objects.order_by('-timestamp')[:50]

    return render(request, 'platform/audits.html', {
        'logs': logs
    })


@login_required
def settings_page(request):
    return render(request, 'platform/settings.html')

@login_required
def add_hospital_admin(request):

    if not (request.user.is_superuser or request.user.role == 'PLATFORM_ADMIN'):
        return redirect('login')

    # Get hospitals without admin
    hospitals_with_admin = User.objects.filter(
        role='HOSPITAL_ADMIN',
        hospital__isnull=False
    ).values_list('hospital_id', flat=True)

    hospitals = Hospital.objects.exclude(id__in=hospitals_with_admin)

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')
        hospital_id = request.POST.get('hospital')

        if User.objects.filter(username=username).exists():
            return render(request, 'platform/add_hospital_admin.html', {
                'hospitals': hospitals,
                'error': "Username already exists."
            })

        hospital = Hospital.objects.get(id=hospital_id)

        new_admin = User.objects.create_user(
            username=username,
            password=password,
            role='HOSPITAL_ADMIN',
            hospital=hospital
        )

        # ✅ Audit log INSIDE POST
        from .models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action=f"Created admin: {new_admin.username} for {hospital.name}"
        )

        return redirect('admins_list')

    return render(request, 'platform/add_hospital_admin.html', {
        'hospitals': hospitals
    })
    



@login_required
def add_hospital(request):
    if not (request.user.is_superuser or request.user.role == 'PLATFORM_ADMIN'):
        return redirect('login')

    if request.method == 'POST':
        hospital_name = request.POST.get('hospital_name')
        location = request.POST.get('location')
        admin_username = request.POST.get('admin_username')
        admin_password = request.POST.get('admin_password')

        # Create Hospital
        hospital = Hospital.objects.create(
            name=hospital_name,
            location=location
        )

        # Create Hospital Admin User
        User.objects.create_user(
            username=admin_username,
            password=admin_password,
            role='HOSPITAL_ADMIN',
            hospital=hospital
        )
        AuditLog.objects.create(
    user=request.user,
    action=f"Created hospital: {hospital.name}"
)

        return redirect('platform_dashboard')

    return render(request, 'platform/add_hospital.html')


from django.shortcuts import get_object_or_404

@login_required
def delete_hospital(request, pk):

    hospital = get_object_or_404(Hospital, pk=pk)

    if request.method == "POST":
        hospital.delete()
        return redirect('clients_list')
    AuditLog.objects.create(
    user=request.user,
    action=f"Deleted hospital: {hospital.name}"
)
    

    return render(request, 'platform/delete_hospital.html', {
        'hospital': hospital
    })

@login_required
def delete_admin(request, pk):

    admin = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        admin.delete()
        return redirect('admins_list')

    return render(request, 'platform/delete_admin.html', {
        'admin': admin
    })

from django.shortcuts import get_object_or_404

@login_required
def edit_hospital(request, pk):
    print("EDIT HIT")
    print("LOGGED USER:", request.user.username)
    print("IS SUPERUSER:", request.user.is_superuser)

    hospital = get_object_or_404(Hospital, pk=pk)

    if request.method == 'POST':
        hospital.name = request.POST.get('name')
        hospital.location = request.POST.get('location')
        hospital.save()
        return redirect('clients_list')

    return render(request, 'platform/edit_hospital.html', {
        'hospital': hospital
    })

@login_required
def edit_admin(request, pk):

    if not (request.user.is_superuser or request.user.role == 'PLATFORM_ADMIN'):
        return redirect('login')

    user = User.objects.get(id=pk)

    if request.method == 'POST':
        user.username = request.POST.get('username')

        new_password = request.POST.get('password')

        if new_password:
            user.set_password(new_password)   # Proper hashing

        user.save()

        return redirect('platform_dashboard')

    return render(request, 'platform/edit_admin.html', {'admin_user': user})
