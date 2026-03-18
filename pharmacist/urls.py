from django.urls import path
from . import views


urlpatterns = [

    path(
        "dashboard/",
        views.pharmacist_dashboard,
        name="pharmacist_dashboard"
    ),

    path(
        "start/<int:token_id>/",
        views.start_preparing,
        name="start_preparing"
    ),

    path(
        "dispatch/<int:token_id>/",
        views.dispatch_medicine,
        name="dispatch_medicine"
    ),

]