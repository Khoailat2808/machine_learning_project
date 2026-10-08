from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


def get_role(user):
    return "admin" if user.is_superuser or user.groups.filter(name="Admin").exists() else "marketer"


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {"username": self.user.username, "role": get_role(self.user)}
        return data


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
