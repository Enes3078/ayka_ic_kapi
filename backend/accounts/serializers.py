from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, TeamAssociate


class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı CRUD serializer."""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'department', 'is_active', 'password',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserReadSerializer(serializers.ModelSerializer):
    """Kullanıcı listesi için salt-okunur serializer (password yok)."""

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'department', 'is_active',
            'created_at', 'updated_at',
        ]


class LoginSerializer(serializers.Serializer):
    """JWT login için serializer."""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password'],
        )
        if not user:
            raise serializers.ValidationError('Kullanıcı adı veya şifre hatalı.')
        if not user.is_active:
            raise serializers.ValidationError('Bu hesap devre dışı bırakılmış.')
        data['user'] = user
        return data


class TeamAssociateSerializer(serializers.ModelSerializer):
    """Hesapsız çalışan serializer."""

    class Meta:
        model = TeamAssociate
        fields = ['id', 'full_name', 'department', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
