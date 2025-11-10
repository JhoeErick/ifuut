from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Quadra, Agendamento, OwnerRequest, OwnerRequestQuadra, OwnerRequestImage

User = get_user_model()


# ---------------- Usuário ----------------
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "tipo", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ---------------- Quadra ----------------
class QuadraSerializer(serializers.ModelSerializer):
    dono = serializers.StringRelatedField(read_only=True)
    dono_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="dono", write_only=True, required=False
    )

    class Meta:
        model = Quadra
        fields = ("id", "nome", "endereco", "descricao", "tipo", "capacidade", "dono", "dono_id")
        read_only_fields = ("id", "dono")


# ---------------- Agendamento ----------------
class AgendamentoSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="usuario", write_only=True, required=False
    )
    quadra = QuadraSerializer(read_only=True)
    quadra_id = serializers.PrimaryKeyRelatedField(
        queryset=Quadra.objects.all(), source="quadra", write_only=True
    )

    class Meta:
        model = Agendamento
        fields = (
            "id",
            "usuario",
            "usuario_id",
            "quadra",
            "quadra_id",
            "data",
            "hora",
            "duracao_minutos",
            "comprovante",
            "tipo_pagamento",
            "confirmado",
            "criado_em",
        )
        read_only_fields = ("id", "usuario", "quadra", "criado_em", "confirmado")


# ---------------- OwnerRequest (Solicitação de Dono) ----------------
class OwnerRequestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerRequestImage
        fields = ("id", "image", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")


class OwnerRequestQuadraSerializer(serializers.ModelSerializer):
    images = OwnerRequestImageSerializer(many=True, read_only=True)

    class Meta:
        model = OwnerRequestQuadra
        fields = (
            "id",
            "nome",
            "tipo",
            "capacidade",
            "surface_type",
            "pile_height_mm",
            "infill_type",
            "infill_depth_mm",
            "shockpad_present",
            "last_replacement_date",
            "maintenance_frequency",
            "surface_condition_rating",
            "certifications",
            "notes",
            "images",
        )
        read_only_fields = ("id", "images")


class OwnerRequestSerializer(serializers.ModelSerializer):
    quadras = OwnerRequestQuadraSerializer(many=True, required=False)
    images = OwnerRequestImageSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OwnerRequest
        fields = (
            "id",
            "user",
            "business_name",
            "business_address",
            "contact_phone",
            "contact_email",
            "description",
            "status",
            "admin_notes",
            "created_at",
            "quadras",
            "images",
        )
        read_only_fields = ("id", "status", "created_at", "user", "images")

    def create(self, validated_data):
        """
        Corrigido: evita erro de múltiplos 'user' e cria quadras relacionadas.
        """
        request = self.context.get("request", None)
        quadras_data = validated_data.pop("quadras", [])

        # define user corretamente sem duplicar
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["user"] = request.user

        # cria o OwnerRequest
        owner_request = OwnerRequest.objects.create(**validated_data)

        # cria quadras relacionadas (se houver)
        for q in quadras_data:
            OwnerRequestQuadra.objects.create(owner_request=owner_request, **q)

        return owner_request
