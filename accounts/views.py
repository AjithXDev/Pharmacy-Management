from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model



User = get_user_model()


def login_view(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # If superuser → treat as platform admin
            if user.is_superuser or user.role == 'PLATFORM_ADMIN':
                return redirect('platform_dashboard')

            elif user.role == 'HOSPITAL_ADMIN':
                return redirect('hospital_dashboard')

            elif user.role == 'PHARMACY_MANAGER':
                return redirect('pharmacy_dashboard')
            
            elif user.role == 'RECEPTION_STAFF':
                return redirect('reception_dashboard')

            else:
                messages.error(request, "Role not assigned properly.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password")
    

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
