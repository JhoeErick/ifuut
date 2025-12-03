from rest_framework import serializers
from .models import Quadra, Agendamento
from django.contrib.auth.models import User


class QuadraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quadra
        fields = "__all__"


class AgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", "")
        )
        user.set_password(validated_data["password"])
        user.save()
        return user
