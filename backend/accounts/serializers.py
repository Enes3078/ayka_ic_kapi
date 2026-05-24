from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, TeamAssociate


class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı CRUD serializer."""
    password = serializers.CharField(write_only=True, min_length=6, required=False)
    team_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )
    assigned_team_ids = serializers.SerializerMethodField(read_only=True)
    assigned_team_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'department', 'is_active', 'password',
            'team_ids', 'assigned_team_ids', 'assigned_team_names',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_assigned_team_ids(self, obj):
        return list(obj.teams.values_list('id', flat=True))

    def get_assigned_team_names(self, obj):
        return list(obj.teams.values_list('name', flat=True))

    def validate_team_ids(self, value):
        from tasks.models import Team
        existing_ids = set(Team.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = sorted(set(value) - existing_ids)
        if missing_ids:
            raise serializers.ValidationError(f'Geçersiz ekip ID: {missing_ids}')
        return value

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Yeni kullanıcı için şifre zorunludur.'})
        return attrs

    def _set_teams(self, user, team_ids):
        if team_ids is None:
            return
        from tasks.models import Team
        teams = Team.objects.filter(id__in=team_ids)
        user.teams.set(teams)

    def create(self, validated_data):
        password = validated_data.pop('password')
        team_ids = validated_data.pop('team_ids', None)
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        self._set_teams(user, team_ids)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        team_ids = validated_data.pop('team_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        self._set_teams(instance, team_ids)
        return instance


class UserReadSerializer(serializers.ModelSerializer):
    """Kullanıcı listesi için salt-okunur serializer (password yok)."""
    assigned_team_ids = serializers.SerializerMethodField()
    assigned_team_names = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'department', 'is_active',
            'assigned_team_ids', 'assigned_team_names',
            'created_at', 'updated_at',
        ]

    def get_assigned_team_ids(self, obj):
        return list(obj.teams.values_list('id', flat=True))

    def get_assigned_team_names(self, obj):
        return list(obj.teams.values_list('name', flat=True))


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
