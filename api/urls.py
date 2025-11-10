# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuadraViewSet,
    AgendamentoViewSet,
    UsuarioCreateView,
    OwnerRequestListCreateView,
    OwnerRequestDetailView,
    admin_counts,  # <-- import do endpoint de contadores
)
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r"quadras", QuadraViewSet, basename="quadra")
router.register(r"agendamentos", AgendamentoViewSet, basename="agendamento")

urlpatterns = [
    # rotas REST principais (quadras, agendamentos)
    path("", include(router.urls)),

    # cadastro de usuário (público)
    path("users/", UsuarioCreateView.as_view(), name="user-register"),

    # solicitações de donos de espaços esportivos
    path("owner-requests/", OwnerRequestListCreateView.as_view(), name="owner-request-list-create"),
    path("owner-requests/<int:pk>/", OwnerRequestDetailView.as_view(), name="owner-request-detail"),

    # rota de contadores para o admin dashboard
    path("admin-counts/", admin_counts, name="admin-counts"),

    # autenticação - token (DRF Token Auth)
    path("api-token-auth/", obtain_auth_token, name="api-token-auth"),

    # autenticação - JWT (Simple JWT)
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
