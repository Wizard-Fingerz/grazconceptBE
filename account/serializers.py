from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User



class UserSerializer(serializers.ModelSerializer):

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
            "gender_name",
        ]




class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'user_type', 'password']

    def create(self, validated_data):
        # pop password from validated_data to handle it securely
        password = validated_data.pop('password')
        user = User(**validated_data)
        print(f"Creating user with email: {user.email}, first name: {user.first_name}, last name: {user.last_name}")
        user.set_password(password)  # hashes the password
        print('Password', user.password)
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

