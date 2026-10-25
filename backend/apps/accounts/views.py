from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {"username": self.user.username}  # D-17: không phân quyền trên web
        return data


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
