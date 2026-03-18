from django.urls import path
from . import views


urlpatterns = [

    #hospital admin
    path('add-pharmacy/', views.add_pharmacy, name='add_pharmacy'),
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    path('hospital-kpi/', views.hospital_kpi, name='hospital_kpi'),
    path('hospital-analytics/', views.hospital_analytics, name='hospital_analytics'),
    path("pharmacies/", views.pharmacy_overview, name="pharmacy_overview"),
    path("pharmacy/toggle/<int:pk>/", views.toggle_pharmacy, name="toggle_pharmacy"),
    path("counters/<int:pharmacy_id>/", views.counter_list, name="counter_list"),
    path("counter/add/<int:pharmacy_id>/", views.add_counter, name="add_counter"),
    path("assign-head/<int:pharmacy_id>/", views.assign_pharmacy_head, name="assign_pharmacy_head"),
    path("counters/", views.all_counters, name="all_counters"),
    path("pharmacy-heads/", views.pharmacy_heads, name="pharmacy_heads"),
    path("counter/toggle/<int:counter_id>/",views.toggle_counter,name="toggle_counter"),  
    path("pharmacy/edit/<int:pk>/", views.edit_pharmacy, name="edit_pharmacy"),
    path("pharmacy/delete/<int:pk>/", views.delete_pharmacy, name="delete_pharmacy"),
    path("counter/edit/<int:pk>/", views.edit_counter, name="edit_counter"),
    path("counter/delete/<int:pk>/", views.delete_counter, name="delete_counter"),
    path("pharmacy-head/remove/<int:user_id>/",views.remove_pharmacy_head,name="remove_pharmacy_head"),
    path("pharmacy-head/create/<int:pharmacy_id>/",views.create_pharmacy_head,name="create_pharmacy_head"),
    path("create-reception/", views.create_reception_staff, name="create_reception"),
    path(
        "add-pharmacist/",
        views.add_pharmacist,
        name="add_pharmacist"
    ),
    
]