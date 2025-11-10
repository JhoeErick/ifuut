from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Painel administrativo (mantém /admin/)
    path("admin/", admin.site.urls),

    # API
    path("api/", include("api.urls")),

    # Home pública (template 'index.html' dentro de BASE_DIR/templates/)
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
]

# servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
