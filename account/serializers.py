from rest_framework import serializers
from django.contrib.auth import authenticate
from wallet.serializers import WalletSerializer
from .models import User

class UserSerializer(serializers.ModelSerializer):
    country_of_residence = serializers.SerializerMethodField()
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
            "user_type_name",
            "full_name",
            "profile_picture_url",
            "gender_name",
            "referred_by",
            "wallet",
        ]
        read_only_fields = [
            "id",
            "custom_id",
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


    def get_country_of_residence(self, obj):
        value = obj.country_of_residence
        if not value:
            return None
        return {
            "code": value.code,
            "name": value.name,
        }


    def get_nationality(self, obj):
        value = obj.nationality
        if not value:
            return None
        return {
            "code": value.code,
            "name": value.name,
        }



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referred_by = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        help_text="The custom_id of the user who referred this client",
        label="Referred By",
        max_length=20,
        required=False,
        default=""
    )

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'user_type',
            'password',
            'referred_by'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
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
