from rest_framework import serializers
from .models import Task, ProductLine, Team, Product, WorkflowTemplate
from accounts.serializers import UserReadSerializer
from accounts.serializers import UserReadSerializer


class TeamSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'department', 'members', 'associates',
            'member_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count() + obj.associates.count()


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplate
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """Katalog ürünleri için serializer."""
    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'duration_minutes',
            'width_mm', 'length_mm', 'additional_dimensions',
            'blade_min_mm', 'blade_max_mm', 'thickness_mm',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductLineSerializer(serializers.ModelSerializer):
    """Üretim kalemi serializer — Task içinde nested olarak kullanılır."""
    total_planned_minutes = serializers.ReadOnlyField()
    completion_rate = serializers.ReadOnlyField()
    current_team_id = serializers.ReadOnlyField()

    class Meta:
        model = ProductLine
        fields = [
            'id', 'product', 'image_base64', 'model_code', 'variant', 'dimension', 'color', 'product_color_code', 
            'blade_depth', 'brief_intro', 'unit_type',
            'quantity', 'qty_produced', 'fire_qty', 'fire_reason', 'fire_image',
            'planning_mode', 'unit_duration_minutes',
            'total_planned_minutes', 'completion_rate',
            'workflow_team_ids', 'workflow_stage_targets',
            'active_product_index', 'stage_done', 'pending_approval', 'current_team_id',
            'notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'total_planned_minutes', 'completion_rate',
            'active_product_index', 'stage_done', 'pending_approval', 'current_team_id',
            'qty_produced', 'fire_qty'
        ]

class ProductLineLogProductionSerializer(serializers.Serializer):
    """Üretim girişi ve Handover için serializer."""
    qty_produced = serializers.IntegerField(min_value=0)
    fire_qty = serializers.IntegerField(min_value=0, default=0)
    fire_reason = serializers.CharField(required=False, default='', allow_blank=True)
    handover = serializers.BooleanField(default=False)



class TaskListSerializer(serializers.ModelSerializer):
    """Görev listesi için hafif serializer (nested ProductLine yok)."""
    owner_name = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    product_line_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority',
            'owner', 'owner_name',
            'assignee', 'assignee_name',
            'team', 'team_name',
            'start_date', 'end_date', 'due_date',
            'planned_hours', 'planned_cost',
            'product_line_count',
            'created_at', 'updated_at',
        ]

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

    def get_assignee_name(self, obj):
        if obj.assignee:
            return obj.assignee.get_full_name() or obj.assignee.username
        return None

    def get_team_name(self, obj):
        return obj.team.name if obj.team else None

    def get_product_line_count(self, obj):
        return obj.product_lines.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Görev detay serializer — nested ProductLine listesi ile birlikte.
    Oluşturma/güncelleme sırasında product_lines iç içe gönderilir.
    """
    product_lines = ProductLineSerializer(many=True)
    owner_detail = UserReadSerializer(source='owner', read_only=True)
    assignee_detail = UserReadSerializer(source='assignee', read_only=True)
    team_detail = TeamSerializer(source='team', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'owner', 'owner_detail',
            'assignee', 'assignee_detail',
            'team', 'team_detail',
            'status', 'priority',
            'start_date', 'end_date', 'due_date',
            'planned_hours', 'planned_cost',
            'product_lines',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_product_lines(self, value):
        """En az 1 üretim kalemi zorunlu."""
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                'En az 1 üretim kalemi (product line) gereklidir.'
            )
        return value

    def validate(self, data):
        """Tarih sıralaması kontrolü."""
        start = data.get('start_date')
        end = data.get('end_date')
        due = data.get('due_date')

        if start and end and start >= end:
            raise serializers.ValidationError(
                {'end_date': 'Bitiş tarihi başlangıçtan sonra olmalı.'}
            )
        if end and due and end >= due:
            raise serializers.ValidationError(
                {'due_date': 'Son tarih, bitiş tarihinden sonra olmalı.'}
            )
        if start and due and start >= due:
            raise serializers.ValidationError(
                {'due_date': 'Son tarih, başlangıç tarihinden sonra olmalı.'}
            )
        return data

    def create(self, validated_data):
        product_lines_data = validated_data.pop('product_lines')
        task = Task(**validated_data)
        # Skip full_clean in save since we already validated
        task.planned_hours = task.planned_hours or 0
        task.planned_cost = task.planned_cost or 0

        task.save()

        for pl_data in product_lines_data:
            ProductLine.objects.create(task=task, **pl_data)

        return task

    def update(self, instance, validated_data):
        product_lines_data = validated_data.pop('product_lines', None)

        # Update task fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update product lines if provided
        if product_lines_data is not None:
            # Delete existing and recreate (simpler for nested updates)
            instance.product_lines.all().delete()
            for pl_data in product_lines_data:
                ProductLine.objects.create(task=instance, **pl_data)

        return instance


class ExcelImportSerializer(serializers.Serializer):
    """Excel dosyası yükleme serializer."""
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                'Sadece .xlsx veya .xls dosyaları kabul edilir.'
            )
        if value.size > 10 * 1024 * 1024:  # 10 MB
            raise serializers.ValidationError(
                'Dosya boyutu 10 MB\'ı aşamaz.'
            )
        return value
