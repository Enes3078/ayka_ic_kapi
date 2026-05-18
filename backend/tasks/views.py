from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from .models import Task, ProductLine, Team
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TeamSerializer,
    ExcelImportSerializer,
    ProductLineSerializer,
    ProductLineLogProductionSerializer,
    ProductSerializer,
    WorkflowTemplateSerializer,
)
from accounts.permissions import IsAdminOrManager, IsAdminRole
from .services.excel_import import parse_excel_file


class TeamViewSet(viewsets.ModelViewSet):
    """Ekip CRUD — /api/tasks/teams/"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManager()]


class ProductViewSet(viewsets.ModelViewSet):
    """Katalog Ürünleri CRUD — /api/tasks/products/"""
    from .models import Product
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManager()]


class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """İş Akışı Şablonları CRUD — /api/tasks/workflow-templates/"""
    from .models import WorkflowTemplate
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManager()]


class TaskViewSet(viewsets.ModelViewSet):
    """
    Görev CRUD — /api/tasks/
    - Liste: TaskListSerializer (hafif)
    - Detay/Create/Update: TaskDetailSerializer (nested ProductLines)
    """
    queryset = Task.objects.select_related(
        'owner', 'assignee', 'team'
    ).prefetch_related('product_lines')

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskDetailSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        if self.action == 'destroy':
            return [IsAdminRole()]
        return [IsAdminOrManager()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtreleme parametreleri
        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('priority'):
            qs = qs.filter(priority=params['priority'])
        if params.get('team'):
            qs = qs.filter(team_id=params['team'])
        if params.get('assignee'):
            qs = qs.filter(assignee_id=params['assignee'])
        if params.get('search'):
            qs = qs.filter(title__icontains=params['search'])
        return qs

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """POST /api/tasks/{id}/change-status/ { status: 'done' }"""
        task = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Task.Status.choices):
            return Response(
                {'detail': f'Geçersiz durum: {new_status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task.status = new_status
        task.save()
        return Response(TaskDetailSerializer(task).data)


class ExcelImportView(APIView):
    """
    POST /api/tasks/import-excel/
    Excel dosyası yükle → Draft veri döner (henüz Task oluşmaz).
    Frontend bu draft'ı TaskModal'da gösterir, kullanıcı ekip seçer ve kaydeder.
    """
    permission_classes = [IsAdminOrManager]
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = ExcelImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data['file']
        try:
            draft = parse_excel_file(file_obj)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(draft, status=status.HTTP_200_OK)


class ProductLineViewSet(viewsets.ModelViewSet):
    """
    Üretim Kalemleri CRUD ve Log Production — /api/tasks/product-lines/
    """
    queryset = ProductLine.objects.select_related('task').all()
    serializer_class = ProductLineSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='log-production')
    def log_production(self, request, pk=None):
        """
        POST /api/tasks/product-lines/{id}/log-production/
        Üretim miktarını artırır, fire kaydeder, gerekirse bir sonraki ekibe devreder (Handover).
        """
        product_line = self.get_object()
        serializer = ProductLineLogProductionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.utils import timezone
        from .models import ProductLineHistory

        qty = serializer.validated_data['qty_produced']
        scrap = serializer.validated_data['fire_qty']
        reason = serializer.validated_data.get('fire_reason', '')
        is_handover = serializer.validated_data.get('handover', False)

        # Miktarları ekle
        product_line.qty_produced += qty
        product_line.fire_qty += scrap
        if reason and not product_line.fire_reason:
            product_line.fire_reason = reason
        elif reason:
            product_line.fire_reason += f" | {reason}"

        # History log oluştur/güncelle
        current_team_id = product_line.current_team_id
        if current_team_id:
            team = Team.objects.get(id=current_team_id)
            history, created = ProductLineHistory.objects.get_or_create(
                product_line=product_line,
                team=team,
                completed_at__isnull=True,
                defaults={'worker': request.user}
            )
            history.qty_produced_at_stage += qty
            history.scrap_qty_at_stage += scrap
            
            if is_handover:
                history.completed_at = timezone.now()
                # Sonraki aşamaya geç
                product_line.active_product_index += 1
                if product_line.active_product_index >= len(product_line.workflow_team_ids):
                    product_line.stage_done = True
                    product_line.pending_approval = True
            history.save()
        else:
            if is_handover:
                product_line.stage_done = True
                product_line.pending_approval = True

        product_line.save()
        return Response(ProductLineSerializer(product_line).data)


class MyTeamQueueView(APIView):
    """
    GET /api/tasks/my-team-queue/
    Sadece kullanıcının bulunduğu ekiplerin sırasında olan kalemleri listeler.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_active:
            return Response([])

        # Kullanıcının bağlı olduğu ekiplerin ID'leri
        team_ids = set(user.teams.values_list('id', flat=True))
        
        # Kullanıcının department string'ini de Team ID'sine çevirip ekle
        if user.department:
            team_obj = Team.objects.filter(name=user.department).first()
            if team_obj:
                team_ids.add(team_obj.id)
        
        # ProductLine'ları kontrol et
        # Not: JSONField üzerinde filtreleme yerine tüm aktif kalemleri çekip Python'da filtreliyoruz 
        # (Küçük veri setleri için OK, performans için özel index gerekir)
        active_lines = ProductLine.objects.filter(
            stage_done=False
        ).select_related('task')

        queue = []
        for line in active_lines:
            if line.current_team_id in team_ids:
                queue.append(line)

        return Response(ProductLineSerializer(queue, many=True).data)


class MyPastTasksView(APIView):
    """
    GET /api/tasks/my-past-tasks/
    Çalışanın kendisinin bitirmiş olduğu görevleri/aşamaları (history log) döner.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import ProductLineHistory
        
        user = request.user
        if not user.is_active:
            return Response([])

        # Çalışanın dahil olduğu bitmiş History kayıtları
        histories = ProductLineHistory.objects.filter(
            worker=user, 
            completed_at__isnull=False
        ).select_related('product_line', 'product_line__task', 'team').order_by('-completed_at')

        results = []
        for h in histories:
            results.append({
                'id': h.id,
                'task_title': h.product_line.task.title,
                'model_code': h.product_line.model_code,
                'team': h.team.name,
                'qty_produced': h.qty_produced_at_stage,
                'scrap_qty': h.scrap_qty_at_stage,
                'completed_at': h.completed_at,
            })

        return Response(results)


class WorkerTrackingView(APIView):
    """
    GET /api/tasks/worker-tracking/
    Çalışan takip dashboard verisi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from accounts.models import CustomUser
        from .models import ProductLineHistory
        from django.db.models import Count, Max, Q
        from django.utils import timezone

        # Aktif çalışanları al
        workers = CustomUser.objects.filter(is_active=True).values(
            'id', 'username', 'first_name', 'last_name',
            'role', 'department',
        )

        result = []
        for w in workers:
            name = f"{w['first_name'] or ''} {w['last_name'] or ''}".strip()
            if not name:
                name = w['username']

            # İşçinin son aktiviteleri
            histories = ProductLineHistory.objects.filter(
                worker_id=w['id']
            ).select_related('product_line', 'team').order_by('-started_at')

            active_task_count = histories.filter(completed_at__isnull=True).count()
            last_activity = histories.aggregate(Max('started_at'))['started_at__max']

            # Son handover
            last_handover_qs = histories.filter(completed_at__isnull=False).first()
            handover_info = None
            is_recent_handover = False

            if last_handover_qs:
                handover_info = {
                    'task_title': f"{last_handover_qs.product_line.model_code} ({last_handover_qs.product_line.task.title})",
                    'team_name': last_handover_qs.team.name,
                    'date': last_handover_qs.completed_at,
                }
                diff = timezone.now() - last_handover_qs.completed_at
                is_recent_handover = diff.total_seconds() < 3600

            result.append({
                'id': w['id'],
                'name': name,
                'username': w['username'],
                'role': w['role'],
                'department': w['department'] or '—',
                'active_task_count': active_task_count,
                'last_activity': last_activity,
                'last_handover': handover_info,
                'is_recent_handover': is_recent_handover,
            })

        # Aktif görev sayısına göre azalan sırala
        result.sort(key=lambda x: x['active_task_count'], reverse=True)

        return Response({
            'workers': result,
            'total_workers': len(result),
            'total_active_tasks': sum(w['active_task_count'] for w in result),
        })

class ReportingDashboardView(APIView):
    """
    GET /api/tasks/dashboard-stats/
    Ana dashboard analitiklerini döner.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services.reporting import ReportingService
        stats = ReportingService.get_dashboard_summary()
        return Response(stats)


class WorkerDetailAPIView(APIView):
    """
    GET /api/tasks/worker-tracking/<id>/
    İşçinin son 14 günlük ve 12 aylık performans grafikleri için verilerini döner.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from accounts.models import CustomUser
        from .models import ProductLineHistory
        from django.utils import timezone
        from datetime import timedelta
        import calendar

        try:
            worker = CustomUser.objects.get(id=pk)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Çalışan bulunamadı'}, status=404)

        histories = ProductLineHistory.objects.filter(worker=worker, completed_at__isnull=False)

        # 14 Günlük Analiz (Tamamlanmış iş sayısı / Gün)
        today = timezone.now().date()
        daily_labels = []
        daily_data = []
        for i in range(13, -1, -1):
            d = today - timedelta(days=i)
            daily_labels.append(d.strftime("%d %b"))
            count = histories.filter(completed_at__date=d).count()
            daily_data.append(count)

        # 12 Aylık Analiz (Tamamlanmış iş sayısı / Ay)
        monthly_labels = []
        monthly_data = []
        current_month = today.replace(day=1)
        for i in range(11, -1, -1):
            m = current_month - timedelta(days=30*i) # Approximate, exact month sub is complex but this works for labels
            # Let's do a better exact month approach
            month_idx = (today.month - 1 - i) % 12 + 1
            year_idx = today.year + ((today.month - 1 - i) // 12)
            monthly_labels.append(f"{calendar.month_abbr[month_idx]} {year_idx}")
            count = histories.filter(completed_at__year=year_idx, completed_at__month=month_idx).count()
            monthly_data.append(count)

        # Aktif Üzerindeki İşler
        active_histories = ProductLineHistory.objects.filter(worker=worker, completed_at__isnull=True).select_related('product_line', 'product_line__task', 'team')
        active_tasks = []
        for ah in active_histories:
            active_tasks.append({
                'id': ah.product_line.id,
                'task_title': ah.product_line.task.title,
                'model_code': ah.product_line.model_code,
                'team': ah.team.name,
                'qty': ah.product_line.quantity,
                'started_at': ah.started_at,
            })

        # Tamamlanmış Geçmiş İşler
        completed_histories = ProductLineHistory.objects.filter(worker=worker, completed_at__isnull=False).select_related('product_line', 'product_line__task', 'team').order_by('-completed_at')
        completed_tasks = []
        for ch in completed_histories:
            completed_tasks.append({
                'id': ch.id,
                'task_title': ch.product_line.task.title,
                'model_code': ch.product_line.model_code,
                'team': ch.team.name,
                'qty_produced': ch.qty_produced_at_stage,
                'scrap_qty': ch.scrap_qty_at_stage,
                'completed_at': ch.completed_at,
            })

        return Response({
            'worker_name': worker.get_full_name() or worker.username,
            'department': worker.department,
            'daily_chart': {'labels': daily_labels, 'data': daily_data},
            'monthly_chart': {'labels': monthly_labels, 'data': monthly_data},
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
        })


class TaskReportView(APIView):
    """
    GET /api/tasks/reports/task-report/
    Görev Raporu (Aylık/Yıllık/Ekip/Kullanıcı/Durum Filtreleri)
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        from .models import Task, ProductLineHistory
        from django.db.models import Sum, F, ExpressionWrapper, fields
        from django.utils import timezone
        
        qs = Task.objects.prefetch_related('product_lines', 'product_lines__histories').all()
        
        # Filtreler
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        team_id = request.query_params.get('team_id')
        user_id = request.query_params.get('user_id')
        status_param = request.query_params.get('status')
        
        if year:
            qs = qs.filter(created_at__year=year)
        if month:
            qs = qs.filter(created_at__month=month)
        if team_id:
            qs = qs.filter(team_id=team_id)
        if user_id:
            qs = qs.filter(assignee_id=user_id)
        if status_param:
            qs = qs.filter(status=status_param)

        total_created = qs.count()
        total_completed = qs.filter(status='done').count()
        
        tasks_data = []
        for task in qs:
            actual_hours = 0
            for pl in task.product_lines.all():
                for history in pl.histories.all():
                    if history.completed_at and history.started_at:
                        diff = (history.completed_at - history.started_at).total_seconds()
                        actual_hours += diff / 3600.0

            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'status': task.get_status_display(),
                'priority': task.get_priority_display(),
                'team': task.team.name if task.team else '-',
                'assignee': task.assignee.get_full_name() or task.assignee.username if task.assignee else '-',
                'owner': task.owner.get_full_name() or task.owner.username,
                'completed_at': task.updated_at if task.status == 'done' else None,
                'planned_hours': float(task.planned_hours),
                'actual_hours': round(actual_hours, 2),
                'product_line_count': task.product_lines.count()
            })

        return Response({
            'aggregate': {
                'total_created': total_created,
                'total_completed': total_completed,
            },
            'tasks': tasks_data
        })


class ProductionReportView(APIView):
    """
    GET /api/tasks/reports/production-report/
    Üretim (Faaliyet) Raporu (Günlük)
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        from .models import ProductLineHistory
        from django.utils import timezone
        import datetime

        date_str = request.query_params.get('date')
        if not date_str:
            target_date = timezone.now().date()
        else:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()

        # O gün başlayan veya biten history'ler
        qs = ProductLineHistory.objects.filter(
            started_at__date__lte=target_date
        ).exclude(
            completed_at__date__lt=target_date
        ).select_related('product_line', 'product_line__task', 'team', 'worker')

        # Filtreleyelim
        logs = []
        team_stats = {}
        total_logs = 0
        total_produced = 0

        for h in qs:
            if h.qty_produced_at_stage > 0:
                team_name = h.team.name
                qty = h.qty_produced_at_stage
                
                total_logs += 1
                total_produced += qty
                team_stats[team_name] = team_stats.get(team_name, 0) + qty

                logs.append({
                    'task_title': h.product_line.task.title,
                    'model_code': h.product_line.model_code,
                    'team': team_name,
                    'worker': h.worker.get_full_name() or h.worker.username if h.worker else '-',
                    'target_qty': h.product_line.quantity,
                    'produced_qty': qty,
                    'scrap_qty': h.scrap_qty_at_stage,
                    'started_at': h.started_at,
                    'completed_at': h.completed_at,
                })

        return Response({
            'aggregate': {
                'target_date': target_date.strftime('%Y-%m-%d'),
                'total_logs': total_logs,
                'total_produced': total_produced,
                'team_stats': [{'team': k, 'qty': v} for k, v in team_stats.items()],
            },
            'logs': logs
        })
