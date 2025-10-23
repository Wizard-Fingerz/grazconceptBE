from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from account.managers import UserManager
from account.utils import generate_filename
from definition.models import TableDropDownDefinition
from definition.permissions.models import UserPermissions
from definition.roles.models import Roles
from django_countries.fields import CountryField
import string
import random

def generate_unique_custom_id():
    """
    Generates a unique 7-character alphanumeric custom_id for User.
    Retries up to 10 times in case of collision (very low probability).
    """
    from account.models import User  # Import inside to avoid circular import

    attempts = 0
    while attempts < 10:
        custom_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        if not User.objects.filter(custom_id=custom_id).exists():
            return custom_id
        attempts += 1
    raise ValueError("Unable to generate unique custom_id after several attempts")

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, null=True, blank=True)
    last_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=17)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_genders',
        limit_choices_to={'table_name': 'gender'}
    )
    current_address = models.TextField(blank=True, null=True)
    country_of_residence = CountryField(blank=True, null=True)
    nationality = CountryField(blank=True, null=True)
    user_type = models.ForeignKey(
        TableDropDownDefinition,
        on_delete=models.CASCADE,
        related_name='user_types',
        limit_choices_to={'table_name': 'user_type'}
    )
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True)
    custom_id = models.CharField(max_length=7, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=generate_filename, blank=True, null=True)
    email = models.EmailField(unique=True)
    extra_permissions = models.ManyToManyField(UserPermissions, related_name='extra_user_permissions', blank=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_users')
    modified_date = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.custom_id:
            self.custom_id = generate_unique_custom_id()
        super().save(*args, **kwargs)

    @property
    def user_type_name(self):
        return self.user_type.term if self.user_type else None

    @property
    def full_name(self):
        # Ensure no double spaces if middle_name is blank or None
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return " ".join(filter(None, names)).strip()

    @property
    def profile_picture_url(self):
        if self.profile_picture:
            try:
                return self.profile_picture.url
            except ValueError:
                return None
        return None

    @property
    def gender_name(self):
        return self.gender.term if self.gender else None

    @property
    def country_of_residence_str(self):
        # Always return a string or None for JSON serialization
        if self.country_of_residence:
            return str(self.country_of_residence)
        return None

    @property
    def nationality_str(self):
        if self.nationality:
            return str(self.nationality)
        return None
