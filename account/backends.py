from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from account.models import User


class EmailBackend(ModelBackend):
    """
    Custom authentication backend to authenticate users by email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email address.
        """
        try:
            # Try to get user by email
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """
        Retrieve a user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
