# api/templatetags/admin_extras.py
from django import template
from django.apps import apps
from django.utils.translation import gettext as _

register = template.Library()

@register.simple_tag
def ifuut_model_counts():
    """
    Retorna lista de dicionários com contadores para o painel.
    Ajuste modelos aqui caso adicione/remova.
    """
    mapping = [
        {"label": _("Quadras"), "model": "api.Quadra", "icon": "🏟️"},
        {"label": _("Agendamentos"), "model": "api.Agendamento", "icon": "📅"},
        {"label": _("Usuários"), "model": "api.Usuario", "icon": "🧍"},
        {"label": _("Solicitações"), "model": "api.OwnerRequest", "icon": "🧾"},
    ]

    results = []
    for item in mapping:
        try:
            Model = apps.get_model(item["model"])
            count = Model.objects.count()
        except Exception:
            count = 0
        results.append({"label": item["label"], "count": count, "icon": item["icon"]})
    return results
