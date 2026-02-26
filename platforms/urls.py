# Platform Pages
from django.urls import path
from . import views

urlpatterns=[
    path('dashboard/', views.platform_dashboard, name='platform_dashboard'),
    path('clients/', views.clients_page, name='clients_list'),
    path('admins/', views.admins_page, name='admins_list'),
    path('audit-logs/', views.audit_logs_page, name='audit_logs'),
    path('settings/', views.settings_page, name='settings'),

    # Hospital Actions
    path('add-hospital/', views.add_hospital, name='add_hospital'),
    path('edit-hospital/<int:pk>/', views.edit_hospital, name='edit_hospital'),
    path('delete-hospital/<int:pk>/', views.delete_hospital, name='delete_hospital'),
    path('export-hospitals/', views.export_hospitals, name='export_hospitals'),

    # Admin Actions
    path('edit-admin/<int:pk>/', views.edit_admin, name='edit_admin'),
    path('delete-admin/<int:pk>/', views.delete_admin, name='delete_admin'),
    path('export-admins/', views.export_admins, name='export_admins'),
    path('add-hospital-admin/', views.add_hospital_admin, name='add_hospital_admin'),
]