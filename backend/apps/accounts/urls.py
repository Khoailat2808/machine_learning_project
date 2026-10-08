from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView

urlpatterns = [
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", TokenRefreshView.as_view()),
]
