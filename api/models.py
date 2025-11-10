from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


# ---------- Usuário ----------
class Usuario(AbstractUser):
    TIPOS = (
        ("comum", "Comum"),
        ("associado", "Associado"),
        ("admin", "Administrador"),
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default="comum", verbose_name=_("Tipo de usuário"))

    def __str__(self):
        return f"{self.username} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = _("Usuário")
        verbose_name_plural = _("Usuários")


# ---------- Quadra ----------
class Quadra(models.Model):
    nome = models.CharField(max_length=255, verbose_name=_("Nome da quadra"))
    endereco = models.CharField(max_length=255, blank=True, verbose_name=_("Endereço"))
    descricao = models.TextField(blank=True, verbose_name=_("Descrição"))
    tipo = models.CharField(max_length=100, blank=True, verbose_name=_("Tipo de quadra"))  # ex: futsal, campo, areia
    dono = models.ForeignKey("Usuario", on_delete=models.CASCADE, related_name="quadras", verbose_name=_("Dono"))
    capacidade = models.IntegerField(null=True, blank=True, verbose_name=_("Capacidade"))

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = _("Quadra")
        verbose_name_plural = _("Quadras")


# ---------- Agendamento ----------
class Agendamento(models.Model):
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE, related_name="agendamentos", verbose_name=_("Usuário"))
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, related_name="agendamentos", verbose_name=_("Quadra"))
    data = models.DateField(verbose_name=_("Data"))
    hora = models.TimeField(verbose_name=_("Hora"))
    duracao_minutos = models.IntegerField(default=60, verbose_name=_("Duração (minutos)"))
    comprovante = models.ImageField(upload_to="comprovantes/", null=True, blank=True, verbose_name=_("Comprovante de pagamento"))
    tipo_pagamento = models.CharField(max_length=50, blank=True, verbose_name=_("Tipo de pagamento"))
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    confirmado = models.BooleanField(default=False, verbose_name=_("Confirmado"))

    class Meta:
        ordering = ["-data", "-hora"]
        verbose_name = _("Agendamento")
        verbose_name_plural = _("Agendamentos")

    def __str__(self):
        return f"{self.quadra.nome} — {self.data} {self.hora} ({self.usuario.username})"


# ---------- Solicitação de Dono (Owner Request) ----------
class OwnerRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendente"),
        ("paid", "Pago"),
        ("approved", "Aprovado"),
        ("rejected", "Rejeitado"),
    )

    user = models.ForeignKey(
        "Usuario",
        on_delete=models.CASCADE,
        related_name="owner_requests",
        verbose_name=_("Usuário solicitante"),
    )
    business_name = models.CharField(max_length=255, verbose_name=_("Nome do estabelecimento"))
    business_address = models.CharField(max_length=400, blank=True, verbose_name=_("Endereço"))
    contact_phone = models.CharField(max_length=50, blank=True, verbose_name=_("Telefone de contato"))
    contact_email = models.EmailField(blank=True, verbose_name=_("E-mail de contato"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name=_("Status"))
    admin_notes = models.TextField(blank=True, verbose_name=_("Anotações do administrador"))

    class Meta:
        verbose_name = _("Solicitação de proprietário")
        verbose_name_plural = _("Solicitações de proprietários")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business_name} ({self.get_status_display()})"


# ---------- Quadras dentro da solicitação ----------
class OwnerRequestQuadra(models.Model):
    owner_request = models.ForeignKey(
        OwnerRequest, on_delete=models.CASCADE, related_name="quadras", verbose_name=_("Solicitação")
    )
    nome = models.CharField(max_length=255, verbose_name=_("Nome da quadra"))
    tipo = models.CharField(max_length=80, blank=True, verbose_name=_("Tipo"))
    capacidade = models.IntegerField(null=True, blank=True, verbose_name=_("Capacidade"))
    surface_type = models.CharField(
        max_length=30,
        choices=(("synthetic", "Sintética"), ("natural", "Natural")),
        default="synthetic",
        verbose_name=_("Tipo de superfície"),
    )
    pile_height_mm = models.IntegerField(null=True, blank=True, verbose_name=_("Altura do pelo (mm)"))
    infill_type = models.CharField(max_length=120, blank=True, verbose_name=_("Tipo de enchimento"))
    infill_depth_mm = models.IntegerField(null=True, blank=True, verbose_name=_("Profundidade do enchimento (mm)"))
    shockpad_present = models.BooleanField(default=False, verbose_name=_("Possui shockpad"))
    last_replacement_date = models.DateField(null=True, blank=True, verbose_name=_("Última substituição"))
    maintenance_frequency = models.CharField(max_length=120, blank=True, verbose_name=_("Frequência de manutenção"))
    surface_condition_rating = models.IntegerField(null=True, blank=True, verbose_name=_("Avaliação da superfície"))
    certifications = models.CharField(max_length=255, blank=True, verbose_name=_("Certificações"))
    notes = models.TextField(blank=True, verbose_name=_("Observações"))

    def __str__(self):
        return f"{self.nome} — {self.owner_request.business_name}"

    class Meta:
        verbose_name = _("Quadra da solicitação")
        verbose_name_plural = _("Quadras da solicitação")


# ---------- Imagens anexadas à solicitação ----------
class OwnerRequestImage(models.Model):
    quadra = models.ForeignKey(
        OwnerRequestQuadra, on_delete=models.CASCADE, related_name="images", null=True, blank=True, verbose_name=_("Quadra")
    )
    owner_request = models.ForeignKey(
        OwnerRequest, on_delete=models.CASCADE, related_name="images", null=True, blank=True, verbose_name=_("Solicitação")
    )
    image = models.ImageField(upload_to="owner_requests/", verbose_name=_("Imagem"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Enviado em"))

    def __str__(self):
        return f"Imagem {self.id} - {self.owner_request.business_name if self.owner_request else 'Sem solicitação'}"

    class Meta:
        verbose_name = _("Imagem da solicitação")
        verbose_name_plural = _("Imagens da solicitação")
