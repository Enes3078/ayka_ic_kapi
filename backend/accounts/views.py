from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, TeamAssociate
from .serializers import (
    UserSerializer,
    UserReadSerializer,
    LoginSerializer,
    TeamAssociateSerializer,
)
from .permissions import IsAdminRole


class LoginView(APIView):
    """
    POST /api/auth/login/
    JWT token döner: { access, refresh, user }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserReadSerializer(user).data,
        })


class MeView(APIView):
    """
    GET /api/auth/me/
    Giriş yapan kullanıcının bilgilerini döner.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserReadSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    """
    /api/auth/users/  — Sadece Admin kullanıcı yönetimi yapabilir.
    Self-delete koruması: Admin kendini silemez.
    """
    queryset = CustomUser.objects.prefetch_related('teams')
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.id == request.user.id:
            return Response(
                {'detail': 'Kendi hesabınızı silemezsiniz.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class TeamAssociateViewSet(viewsets.ModelViewSet):
    """
    /api/auth/associates/  — Hesapsız çalışan CRUD.
    Admin ve Manager erişebilir.
    """
    queryset = TeamAssociate.objects.all()
    serializer_class = TeamAssociateSerializer

    def get_permissions(self):
        from .permissions import IsAdminOrManager
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManager()]
