from rest_framework import serializers
from django.contrib.auth import authenticate

from wallet.serializers import WalletSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    # Use source to directly get the string representation from the model property
    country_of_residence = serializers.CharField(
        source="country_of_residence_str", read_only=True)
    nationality = serializers.SerializerMethodField()
    wallet = WalletSerializer()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "gender",
            "current_address",
            "country_of_residence",
            "nationality",
            "user_type",
            "role",
            "custom_id",
            "profile_picture",
            "email",
            "extra_permissions",
            "is_deleted",
            "is_active",
            "is_staff",
            "created_by",
            "created_date",
            "modified_by",
            "modified_date",
            "last_login",
            # computed / helper fields
            "user_type_name",
            "full_name",
            "profile_picture_url",
            "gender_name",
            "referred_by",
            "wallet",
        ]
        read_only_fields = [
            "id",
            "custom_id",          # if auto-generated
            "created_by",
            "created_date",
            "modified_by",
            "modified_date",
            "last_login",
            "user_type_name",
            "full_name",
            "profile_picture_url",
            "wallet",
            "gender_name",
        ]

    def get_nationality(self, obj):
        nationality = getattr(obj, "nationality", None)
        if nationality:
            return str(nationality)
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'user_type', 'password', "referred_by",]

    def create(self, validated_data):
        password = validated_data.pop('password')
        referred_by = validated_data.get('referred_by', None)

        # If referred_by is present and is not a User instance, try converting to a User instance by pk
        if referred_by and not isinstance(referred_by, User):
            try:
                referred_by_user = User.objects.get(pk=referred_by)
            except User.DoesNotExist:
                referred_by_user = None
            validated_data['referred_by'] = referred_by_user

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        data['user'] = user
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
