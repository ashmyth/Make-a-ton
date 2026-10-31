from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import authenticate, login, logout


class CurrentUserView(APIView):
    """
    Returns authenticated user details matching Teammate 1 contract:
    { id, email, first_name, last_name, full_name, role, is_active, customer_id }
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "customer_id": user.customer_id,
        })


class LoginView(APIView):
    """Simple session login for console staff and portal customers."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"detail": "Account deactivated."}, status=status.HTTP_403_FORBIDDEN)

        login(request, user)
        return Response({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "customer_id": user.customer_id,
        })


class LogoutView(APIView):
    """Session logout."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully."})
