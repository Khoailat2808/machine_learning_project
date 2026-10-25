from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/summary", views.dashboard_summary),
    path("model/info", views.model_info),
]
