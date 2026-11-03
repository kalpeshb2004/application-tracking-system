from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "email", "role", "password")
        read_only_fields = ("id", "role")   # client can NEVER set role
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 6, "max_length": 50},
        }

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        # create_user hashes the password. Never save raw password.
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "email", "role")