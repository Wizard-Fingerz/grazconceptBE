from rest_framework import serializers
from django.contrib.auth import authenticate
from wallet.serializers import WalletSerializer
from .models import User, UserProfile


def _country_repr(val):
    if not val:
        return None
    return {"code": val.code, "name": val.name}


# ── Extended profile (nested) ────────────────────────────────────────────────

class UserProfileExtendedSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "passport_number", "passport_expiry_date", "nin", "bvn",
            "highest_qualification", "graduation_year",
            "previous_university", "previous_course_of_study", "cgpa",
            "previous_job_title", "previous_employer",
            "years_of_experience", "year_left_previous_job",
            "emergency_contact_name", "emergency_contact_relationship",
            "emergency_contact_phone",
            "travel_history", "previous_visa_applications", "previous_visa_details",
        ]


# ── Full profile read (GET /users/profile/) ──────────────────────────────────

class UserProfileDetailSerializer(serializers.ModelSerializer):
    """All User fields + extended profile fields flattened."""
    country_of_residence = serializers.SerializerMethodField()
    nationality = serializers.SerializerMethodField()
    wallet = WalletSerializer(read_only=True)

    # Extended fields
    passport_number = serializers.SerializerMethodField()
    passport_expiry_date = serializers.SerializerMethodField()
    nin = serializers.SerializerMethodField()
    bvn = serializers.SerializerMethodField()
    highest_qualification = serializers.SerializerMethodField()
    graduation_year = serializers.SerializerMethodField()
    previous_university = serializers.SerializerMethodField()
    previous_course_of_study = serializers.SerializerMethodField()
    cgpa = serializers.SerializerMethodField()
    previous_job_title = serializers.SerializerMethodField()
    previous_employer = serializers.SerializerMethodField()
    years_of_experience = serializers.SerializerMethodField()
    year_left_previous_job = serializers.SerializerMethodField()
    emergency_contact_name = serializers.SerializerMethodField()
    emergency_contact_relationship = serializers.SerializerMethodField()
    emergency_contact_phone = serializers.SerializerMethodField()
    travel_history = serializers.SerializerMethodField()
    previous_visa_applications = serializers.SerializerMethodField()
    previous_visa_details = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "first_name", "middle_name", "last_name",
            "phone_number", "date_of_birth", "gender", "gender_name",
            "current_address", "country_of_residence", "nationality",
            "user_type", "user_type_name", "role", "custom_id",
            "profile_picture", "profile_picture_url",
            "email", "full_name",
            "is_deleted", "is_active", "is_staff",
            "created_by", "created_date", "modified_by", "modified_date",
            "last_login", "referred_by", "wallet",
            "passport_number", "passport_expiry_date", "nin", "bvn",
            "highest_qualification", "graduation_year",
            "previous_university", "previous_course_of_study", "cgpa",
            "previous_job_title", "previous_employer",
            "years_of_experience", "year_left_previous_job",
            "emergency_contact_name", "emergency_contact_relationship",
            "emergency_contact_phone",
            "travel_history", "previous_visa_applications", "previous_visa_details",
        ]

    def get_country_of_residence(self, obj):
        return _country_repr(obj.country_of_residence)

    def get_nationality(self, obj):
        return _country_repr(obj.nationality)

    def _ep(self, obj):
        try:
            return obj.extended_profile
        except UserProfile.DoesNotExist:
            return None

    def get_passport_number(self, obj):
        ep = self._ep(obj); return ep.passport_number if ep else None

    def get_passport_expiry_date(self, obj):
        ep = self._ep(obj)
        return str(ep.passport_expiry_date) if ep and ep.passport_expiry_date else None

    def get_nin(self, obj):
        ep = self._ep(obj); return ep.nin if ep else None

    def get_bvn(self, obj):
        ep = self._ep(obj); return ep.bvn if ep else None

    def get_highest_qualification(self, obj):
        ep = self._ep(obj); return ep.highest_qualification if ep else None

    def get_graduation_year(self, obj):
        ep = self._ep(obj); return ep.graduation_year if ep else None

    def get_previous_university(self, obj):
        ep = self._ep(obj); return ep.previous_university if ep else None

    def get_previous_course_of_study(self, obj):
        ep = self._ep(obj); return ep.previous_course_of_study if ep else None

    def get_cgpa(self, obj):
        ep = self._ep(obj); return ep.cgpa if ep else None

    def get_previous_job_title(self, obj):
        ep = self._ep(obj); return ep.previous_job_title if ep else None

    def get_previous_employer(self, obj):
        ep = self._ep(obj); return ep.previous_employer if ep else None

    def get_years_of_experience(self, obj):
        ep = self._ep(obj); return ep.years_of_experience if ep else None

    def get_year_left_previous_job(self, obj):
        ep = self._ep(obj); return ep.year_left_previous_job if ep else None

    def get_emergency_contact_name(self, obj):
        ep = self._ep(obj); return ep.emergency_contact_name if ep else None

    def get_emergency_contact_relationship(self, obj):
        ep = self._ep(obj); return ep.emergency_contact_relationship if ep else None

    def get_emergency_contact_phone(self, obj):
        ep = self._ep(obj); return ep.emergency_contact_phone if ep else None

    def get_travel_history(self, obj):
        ep = self._ep(obj); return ep.travel_history if ep else None

    def get_previous_visa_applications(self, obj):
        ep = self._ep(obj); return ep.previous_visa_applications if ep else False

    def get_previous_visa_details(self, obj):
        ep = self._ep(obj); return ep.previous_visa_details if ep else None


# ── Fields split ──────────────────────────────────────────────────────────────

USER_WRITABLE = [
    "first_name", "middle_name", "last_name", "phone_number",
    "date_of_birth", "gender", "nationality", "country_of_residence",
    "current_address",
]

EXTENDED_FIELDS = [
    "passport_number", "passport_expiry_date", "nin", "bvn",
    "highest_qualification", "graduation_year",
    "previous_university", "previous_course_of_study", "cgpa",
    "previous_job_title", "previous_employer",
    "years_of_experience", "year_left_previous_job",
    "emergency_contact_name", "emergency_contact_relationship",
    "emergency_contact_phone",
    "travel_history", "previous_visa_applications", "previous_visa_details",
]


# ── PATCH serializer (PATCH /users/profile/update/) ──────────────────────────

class UserProfileUpdateSerializer(serializers.Serializer):
    """Flat partial-update serializer for User + UserProfile fields."""
    first_name = serializers.CharField(max_length=200, required=False)
    middle_name = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(max_length=200, required=False)
    phone_number = serializers.CharField(max_length=17, required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    nationality = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    country_of_residence = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    current_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    passport_number = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    passport_expiry_date = serializers.DateField(required=False, allow_null=True)
    nin = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    bvn = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    highest_qualification = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    graduation_year = serializers.IntegerField(required=False, allow_null=True, min_value=1900, max_value=2100)
    previous_university = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    previous_course_of_study = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    cgpa = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    previous_job_title = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    previous_employer = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    years_of_experience = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    year_left_previous_job = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)

    emergency_contact_name = serializers.CharField(max_length=200, required=False, allow_blank=True, allow_null=True)
    emergency_contact_relationship = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    emergency_contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    travel_history = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    previous_visa_applications = serializers.BooleanField(required=False)
    previous_visa_details = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def update(self, instance, validated_data):
        # User model fields
        user_updates = {}
        for field in USER_WRITABLE:
            if field not in validated_data:
                continue
            if field == "gender":
                gender_val = validated_data[field]
                if gender_val:
                    from definition.models import TableDropDownDefinition
                    gender_obj = TableDropDownDefinition.objects.filter(
                        table_name='gender', term__iexact=gender_val
                    ).first()
                    user_updates["gender_id"] = gender_obj.pk if gender_obj else None
                else:
                    user_updates["gender_id"] = None
            else:
                user_updates[field] = validated_data[field]

        if user_updates:
            for attr, val in user_updates.items():
                setattr(instance, attr, val)
            instance.save(update_fields=list(user_updates.keys()))

        # Extended profile fields
        ep_updates = {f: validated_data[f] for f in EXTENDED_FIELDS if f in validated_data}
        if ep_updates:
            ep, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, val in ep_updates.items():
                setattr(ep, attr, val)
            ep.save(update_fields=list(ep_updates.keys()))

        return instance


# ── Legacy UserSerializer (kept for admin ViewSet) ────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    country_of_residence = serializers.SerializerMethodField()
    nationality = serializers.SerializerMethodField()
    wallet = WalletSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "first_name", "middle_name", "last_name",
            "phone_number", "date_of_birth", "gender",
            "current_address", "country_of_residence", "nationality",
            "user_type", "role", "custom_id",
            "profile_picture", "email", "extra_permissions",
            "is_deleted", "is_active", "is_staff",
            "created_by", "created_date", "modified_by", "modified_date",
            "last_login", "user_type_name", "full_name",
            "profile_picture_url", "gender_name", "referred_by", "wallet",
        ]
        read_only_fields = [
            "id", "custom_id", "created_by", "created_date",
            "modified_by", "modified_date", "last_login",
            "user_type_name", "full_name", "profile_picture_url",
            "wallet", "gender_name",
        ]

    def get_country_of_residence(self, obj):
        return _country_repr(obj.country_of_residence)

    def get_nationality(self, obj):
        return _country_repr(obj.nationality)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referred_by = serializers.CharField(
        allow_blank=True, allow_null=True,
        help_text="The custom_id of the user who referred this client",
        label="Referred By", max_length=20, required=False, default=""
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "user_type", "password", "referred_by"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data["user"] = user
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
