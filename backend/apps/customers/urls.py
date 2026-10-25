from django.urls import path

from . import views

urlpatterns = [
    path("customers", views.customer_list),
    path("customers/export", views.customer_export),
    path("customers/<str:customer_id>", views.customer_detail),
]
