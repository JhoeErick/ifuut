# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    Usuario,
    Quadra,
    Agendamento,
    OwnerRequest,
    OwnerRequestQuadra,
    OwnerRequestImage,
)

# ---------- PERSONALIZAÇÃO GERAL DO ADMIN ----------
admin.site.site_header = "🏟️ IFUUT — Painel Administrativo"
admin.site.site_title = "IFUUT Administração"
admin.site.index_title = "Painel de Controle Esportivo"
admin.site.site_url = "/"
admin.site.enable_nav_sidebar = True


# ---------- MIXIN VISUAL ----------
class IFUUTAdminMixin:
    """Mixin para carregar CSS e JS personalizados no admin IFUUT.
    Ajuste os nomes dos arquivos se você usar outros nomes na pasta static/admin_custom/.
    """
    class Media:
        css = {
            "all": (
                "admin_custom/css/ifuut_admin.css",
                "admin_custom/css/ifuut_admin_extra.css",
            )
        }
        js = ("admin_custom/js/ifuut_admin.js",)


# ---------- USUÁRIO ----------
@admin.register(Usuario)
class CustomUserAdmin(UserAdmin, IFUUTAdminMixin):
    model = Usuario
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("tipo",)}),)
    list_display = ("username", "email", "first_name", "last_name", "tipo", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("tipo", "is_staff", "is_superuser", "is_active")
    ordering = ("username",)
    # rótulos em português (útil se você exibir via código)
    verbose_name = _("Usuário")
    verbose_name_plural = _("Usuários")


# ---------- QUADRA ----------
@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin, IFUUTAdminMixin):
    list_display = ("nome", "tipo", "dono", "endereco", "capacidade")
    search_fields = ("nome", "tipo", "dono__username", "endereco")
    list_filter = ("tipo",)
    ordering = ("nome",)
    verbose_name = _("Quadra")
    verbose_name_plural = _("Quadras")


# ---------- AGENDAMENTO ----------
@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin, IFUUTAdminMixin):
    list_display = ("quadra", "usuario", "data", "hora", "confirmado", "criado_em")
    list_filter = ("confirmado", "data")
    search_fields = ("quadra__nome", "usuario__username")
    ordering = ("-data", "-hora")
    verbose_name = _("Agendamento")
    verbose_name_plural = _("Agendamentos")


# ---------- INLINE: QUADRAS NAS SOLICITAÇÕES ----------
class OwnerRequestQuadraInline(admin.TabularInline):
    model = OwnerRequestQuadra
    extra = 0
    fields = (
        "nome",
        "tipo",
        "capacidade",
        "surface_type",
        "pile_height_mm",
        "infill_type",
        "infill_depth_mm",
        "last_replacement_date",
        "surface_condition_rating",
    )
    verbose_name = _("Quadra da solicitação")
    verbose_name_plural = _("Quadras da solicitação")


# ---------- INLINE: IMAGENS ----------
class OwnerRequestImageInline(admin.TabularInline):
    model = OwnerRequestImage
    extra = 0
    readonly_fields = ("uploaded_at", "preview")
    fields = ("image", "preview", "uploaded_at")

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 150px; height: auto; border-radius: 8px; box-shadow: 0 0 6px #00ff88;">',
                obj.image.url,
            )
        return _("(Sem imagem)")

    preview.short_description = _("Pré-visualização")


# ---------- SOLICITAÇÃO DE DONO ----------
@admin.register(OwnerRequest)
class OwnerRequestAdmin(admin.ModelAdmin, IFUUTAdminMixin):
    list_display = ("business_name", "user", "status", "created_at", "contact_phone")
    list_filter = ("status", "created_at")
    search_fields = ("business_name", "user__username", "contact_email", "contact_phone")
    readonly_fields = ("created_at",)
    inlines = [OwnerRequestQuadraInline, OwnerRequestImageInline]
    actions = ["mark_paid", "approve_request", "reject_request"]
    verbose_name = _("Solicitação de proprietário")
    verbose_name_plural = _("Solicitações de proprietários")

    # ---------- AÇÕES ----------
    def mark_paid(self, request, queryset):
        updated = queryset.update(status="paid")
        self.message_user(request, f"{updated} solicitação(ões) marcadas como Pagas.")
    mark_paid.short_description = "✅ Marcar como Pago"

    def approve_request(self, request, queryset):
        approved = 0
        from .models import Quadra  # import local para evitar circularidade
        for obj in queryset:
            obj.status = "approved"
            obj.save()
            usr = obj.user
            if usr:
                usr.tipo = "admin"
                usr.save()
            approved += 1
            # cria quadras reais com base na solicitação (caso haja)
            for q in obj.quadras.all():
                Quadra.objects.create(
                    nome=q.nome,
                    endereco=obj.business_address or "",
                    descricao=q.notes or "",
                    tipo=q.tipo or "",
                    dono=usr,
                    capacidade=q.capacidade or None,
                )
        self.message_user(request, f"{approved} solicitação(ões) aprovadas e usuários promovidos.")
    approve_request.short_description = "🟩 Aprovar e promover usuário (cria Quadras)"

    def reject_request(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(request, f"{updated} solicitação(ões) rejeitadas.")
    reject_request.short_description = "❌ Rejeitar solicitações"
