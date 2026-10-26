from django.urls import path

from . import predict, views

urlpatterns = [
    path("dashboard/summary", views.dashboard_summary),
    path("model/info", views.model_info),
    path("journeys", views.journeys),
    path("predict", predict.predict),
]
