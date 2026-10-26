from django.urls import path

from . import views

urlpatterns = [
    path("campaigns/preview", views.preview),
    path("campaigns/export", views.export),
]
