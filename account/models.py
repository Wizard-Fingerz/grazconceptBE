from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from account.managers import UserManager
from definition.models import TableDropDownDefinition
from definition.permissions.models import UserPermissions
from definition.roles.models import Roles
from django_countries.fields import CountryField
from cloudinary.models import CloudinaryField
from globalconceptBE.validators import validate_image_file
import string
import random


def generate_unique_custom_id():
    from account.models import User
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
        null=True, blank=True,
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
    profile_picture = CloudinaryField('image', blank=True, null=True, validators=[validate_image_file])
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
    referred_by = models.CharField(
        max_length=20, blank=True, null=True,
        db_column='referred_by',
        help_text="The custom_id of the user who referred this client",
        verbose_name="Referred By"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.referred_by and self.custom_id and self.referred_by == self.custom_id:
            raise ValueError("A user cannot refer themselves.")
        if not self.custom_id:
            self.custom_id = generate_unique_custom_id()
        super().save(*args, **kwargs)

    @property
    def user_type_name(self):
        return self.user_type.term if self.user_type else None

    @property
    def full_name(self):
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
            except Exception:
                return None
        return None

    @property
    def gender_name(self):
        return self.gender.term if self.gender else None

    @property
    def country_of_residence_str(self):
        if self.country_of_residence:
            return str(self.country_of_residence)
        return None

    @property
    def nationality_str(self):
        if self.nationality:
            return str(self.nationality)
        return None

    @property
    def referred_by_code(self):
        return self.referred_by or None

    @property
    def referred_by_email(self):
        if self.referred_by:
            try:
                ref_user = User.objects.get(custom_id=self.referred_by)
                if ref_user.pk != self.pk:
                    return ref_user.email
            except User.DoesNotExist:
                return None
        return None

    @property
    def wallet(self):
        try:
            from wallet.models import Wallet
        except ImportError:
            return None
        try:
            w = Wallet.objects.get(user=self)
            return {f.name: getattr(w, f.name) for f in w._meta.fields}
        except Wallet.DoesNotExist:
            return None
        except Exception:
            return None


class UserProfile(models.Model):
    """
    Extended profile data for a User: passport/identity, education,
    employment, emergency contact, and travel/visa history.
    Auto-created via post_save signal when a User is created.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='extended_profile')

    # Identity / Passport
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    passport_expiry_date = models.DateField(blank=True, null=True)
    nin = models.CharField(max_length=20, blank=True, null=True, verbose_name="NIN")
    bvn = models.CharField(max_length=20, blank=True, null=True, verbose_name="BVN")

    # Education
    highest_qualification = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    previous_university = models.CharField(max_length=255, blank=True, null=True)
    previous_course_of_study = models.CharField(max_length=255, blank=True, null=True)
    cgpa = models.CharField(max_length=20, blank=True, null=True)

    # Employment
    previous_job_title = models.CharField(max_length=255, blank=True, null=True)
    previous_employer = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    year_left_previous_job = models.CharField(max_length=10, blank=True, null=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)

    # Travel & Visa History
    travel_history = models.TextField(blank=True, null=True)
    previous_visa_applications = models.BooleanField(default=False)
    previous_visa_details = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Extended Profile"
        verbose_name_plural = "User Extended Profiles"

    def __str__(self):
        return f"Profile({self.user.email})"
