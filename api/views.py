# api/views.py
from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics, permissions, status
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quadra, Agendamento, OwnerRequest, OwnerRequestImage
from .serializers import (
    UsuarioSerializer,
    QuadraSerializer,
    AgendamentoSerializer,
    OwnerRequestSerializer,
)
import json

# imports adicionais para o endpoint de contadores
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required

User = get_user_model()


class UsuarioCreateView(generics.CreateAPIView):
    """Endpoint para cadastro de usuários (public)."""
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.AllowAny]


class QuadraViewSet(viewsets.ModelViewSet):
    """CRUD de Quadras. Criação somente para usuário autenticado (será dono)."""
    queryset = Quadra.objects.all()
    serializer_class = QuadraSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # se o campo dono_id não for enviado, usa o usuário logado
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(dono=self.request.user)
        else:
            serializer.save()


class AgendamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Agendamentos.
    - Usuários autenticados podem criar.
    - Usuários veem apenas seus agendamentos (exceto staff/admin).
    """
    queryset = Agendamento.objects.select_related("quadra", "usuario").all()
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_authenticated:
            # staff vê todos, usuários comuns só os seus
            if user.is_staff:
                return qs
            return qs.filter(usuario=user)
        # não autenticados - sem agendamentos (ou poderia retornar vazios)
        return qs.none()

    def perform_create(self, serializer):
        # define o usuário do agendamento como o usuário logado
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(usuario=self.request.user)
        else:
            # fallback — não deveria acontecer pois permission exige auth para criar
            serializer.save()


# ---------------- OwnerRequest views ----------------
class OwnerRequestListCreateView(generics.ListCreateAPIView):
    """
    GET -> lista OwnerRequests
    POST -> cria OwnerRequest (aceita multipart/form-data; 'quadras' pode vir como JSON string)
    """
    queryset = OwnerRequest.objects.all().order_by('-created_at')
    serializer_class = OwnerRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # leitura pública, criação permitida também

    def create(self, request, *args, **kwargs):
        """
        Mantém a lógica presente na sua antiga post():
        - aceita 'quadras' como string JSON e faz parse antes da validação
        - utiliza serializer com contexto request (para poder usar request.user se necessário)
        - depois de salvar o OwnerRequest, processa imagens multipart (campo 'images')
        """
        data = request.data.copy()

        # se 'quadras' vier como string (JSON), parsear para lista
        quadras_json = data.get("quadras")
        if quadras_json and isinstance(quadras_json, str):
            try:
                # QueryDict pode ser imutável; tentar tornar mutável
                try:
                    data._mutable = True
                except Exception:
                    data = dict(data)
                parsed = json.loads(quadras_json)
                data["quadras"] = parsed
            except Exception:
                # se falhar, deixar como estava (serializer lidará com validação)
                pass

        # usar serializer com contexto request (para pegar request.user se autenticado)
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # salvar o owner_request (o serializer deve lidar com quadras aninhadas)
        # tenta passar user se autenticado
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            owner_request = serializer.save(user=user)
        else:
            owner_request = serializer.save()

        # processar imagens multipart (campo 'images' pode ter vários arquivos)
        files = request.FILES.getlist("images")
        for f in files:
            OwnerRequestImage.objects.create(owner_request=owner_request, image=f)

        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(owner_request).data, status=status.HTTP_201_CREATED, headers=headers)


class OwnerRequestDetailView(generics.RetrieveAPIView):
    """Detalhe de uma OwnerRequest (GET /owner-requests/<pk>/)."""
    queryset = OwnerRequest.objects.all()
    serializer_class = OwnerRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# Compatibilidade com código anterior que importava OwnerRequestCreateView
OwnerRequestCreateView = OwnerRequestListCreateView


# ---------------- Endpoint auxiliar: contadores do admin ----------------
@require_GET
@staff_member_required
def admin_counts(request):
    """
    Retorna JSON com contadores para o dashboard do admin.
    Acesso: staff (usuários logados no admin).
    """
    try:
        counts = {
            "quadras": Quadra.objects.count(),
            "agendamentos": Agendamento.objects.count(),
            "solicitacoes": OwnerRequest.objects.count(),
            "usuarios": get_user_model().objects.count(),
            "solicitacoes_pendentes": OwnerRequest.objects.filter(status="pending").count(),
        }
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)

    return JsonResponse(counts)
