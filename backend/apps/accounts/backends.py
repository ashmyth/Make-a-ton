from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class BrightloopBackend(ModelBackend):
    """Session user loader that also fetches the linked customer in one query."""

    def get_user(self, user_id):
        User = get_user_model()
        try:
            user = User.objects.select_related("customer_profile").get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return None
        return user if self.user_can_authenticate(user) else None
