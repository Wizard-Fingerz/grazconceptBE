from django.contrib.auth.models import BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager for User model with enforced user_type."""

    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        # ✅ Enforce that user_type is provided
        if not extra_fields.get('user_type'):
            raise ValueError('Users must have a user_type')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # Set password
        if password:
            user.set_password(password)
        else:
            user.set_password("mypassword")  # Default password

        # Optionally set role
        if role:
            from definition.roles.models import Roles
            user.role = Roles.objects.get(name=role)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # ✅ Enforce and auto-fetch Admin user_type if not provided
        if not extra_fields.get('user_type'):
            from definition.models import TableDropDownDefinition
            admin_type = TableDropDownDefinition.objects.filter(
                table_name='user_type', term='Admin'
            ).first()
            if not admin_type:
                raise ValueError("Default 'Admin' user_type not found. Please create it first.")
            extra_fields['user_type'] = admin_type

        return self.create_user(email, password, **extra_fields)


# ✅ Role-based managers
class SuperAdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role__name__iexact='superadmin')


class ManagersManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_manager=True, is_staff=True)


class AdministratorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role__name__iexact='administrator')
