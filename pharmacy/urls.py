from django.urls import path
from . import views

urlpatterns = [
 path("dashboard/", views.pharmacy_dashboard, name="pharmacy_dashboard"),
    path("counters/", views.counter_list, name="counter_list"),
    path("counters/add/", views.add_counter, name="add_counter"),
    path("waiting/", views.waiting_list, name="waiting_list"),
    path("complete/<int:token_id>/", views.complete_billing, name="complete_billing"),
    path("toggle/<int:counter_id>/", views.toggle_counter, name="toggle_counter"),
    path("prepare/", views.prepare_list, name="prepare_list"),
    path("start/<int:prep_id>/", views.start_prepare, name="start_prepare"),
    path("finish/<int:prep_id>/", views.finish_prepare, name="finish_prepare"),
  
    
]