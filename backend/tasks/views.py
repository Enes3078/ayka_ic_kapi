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
        
        used_stock_item_id = serializer.validated_data.get('used_stock_item_id')
        used_stock_quantity = serializer.validated_data.get('used_stock_quantity')
        used_stocks = serializer.validated_data.get('used_stocks', [])

        from stock.models import StockTransaction
        from django.core.exceptions import ValidationError as DjangoValidationError

        report_date = serializer.validated_data.get('report_date')

        # Eski tekli stok düşümü (geriye dönük uyumluluk için)
        if used_stock_item_id and used_stock_quantity:
            used_stocks.append({'item_id': used_stock_item_id, 'quantity': used_stock_quantity})

        # Çoklu stok düşümü
        for stock_usage in used_stocks:
            item_id = stock_usage.get('item_id')
            sqty = stock_usage.get('quantity')
            if item_id and sqty:
                try:
                    StockTransaction.create_exit(
                        stock_item_id=item_id,
                        quantity=sqty,
                        user=request.user,
                        notes=f"Otomatik Üretim Tüketimi ({qty} adet üretim için)",
                        usage_location=f"Görev: {product_line.task.title} - Model: {product_line.model_code}"
                    )
                except Exception as e:
                    if isinstance(e, DjangoValidationError):
                        msg = e.message if hasattr(e, 'message') else str(e)
                        return Response({'detail': f'Stok düşülemedi: {msg}'}, status=status.HTTP_400_BAD_REQUEST)
                    return Response({'detail': f'Stok işlem hatası: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

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
            
            if created and report_date:
                from datetime import datetime, time
                history.started_at = timezone.make_aware(datetime.combine(report_date, time(17, 0)))

            history.qty_produced_at_stage += qty
            history.scrap_qty_at_stage += scrap
            
            if is_handover:
                if report_date:
                    from datetime import datetime, time
                    history.completed_at = timezone.make_aware(datetime.combine(report_date, time(17, 30)))
                else:
                    history.completed_at = timezone.now()
                # Sonraki aşamaya geç
                product_line.active_product_index += 1
                if product_line.active_product_index >= len(product_line.workflow_team_ids):
                    product_line.stage_done = True
                    product_line.pending_approval = True
            
            # CNC vb. Ekstra Rapor Alanlarını Kaydet
            if serializer.validated_data.get('working_hours'):
                history.working_hours = serializer.validated_data['working_hours']
            if serializer.validated_data.get('work_description'):
                history.work_description = serializer.validated_data['work_description']
            if serializer.validated_data.get('scrap_location'):
                history.scrap_location = serializer.validated_data['scrap_location']
            if serializer.validated_data.get('activity_notes'):
                history.activity_notes = serializer.validated_data['activity_notes']
                
            # PVC ve Giben
            if serializer.validated_data.get('pvc_color'):
                history.pvc_color = serializer.validated_data['pvc_color']
            if serializer.validated_data.get('pvc_roll_size'):
                history.pvc_roll_size = serializer.validated_data['pvc_roll_size']
            if serializer.validated_data.get('pvc_meters'):
                history.pvc_meters = serializer.validated_data['pvc_meters']
            if serializer.validated_data.get('pvc_cut_size'):
                history.pvc_cut_size = serializer.validated_data['pvc_cut_size']
            if serializer.validated_data.get('giben_plate_size'):
                history.giben_plate_size = serializer.validated_data['giben_plate_size']
                
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
    Çalışanın ekibinde aktif olan görevleri, görev bazlı gruplandırılmış kalemlerle döner.
    Her kalemde hedef, üretilen ve KALAN miktarlar yer alır.
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
        
        # Aktif (tamamlanmamış) kalemleri çek
        active_lines = ProductLine.objects.filter(
            stage_done=False
        ).select_related('task', 'task__owner', 'task__team')

        # Kullanıcının ekibinde olan VEYA BİR SONRAKİ adımda (yaklaşan) olan kalemleri filtrele
        my_lines = []
        for line in active_lines:
            is_current = line.current_team_id in team_ids
            
            # Yaklaşan görev kontrolü
            is_upcoming = False
            if line.workflow_team_ids and line.active_product_index + 1 < len(line.workflow_team_ids):
                next_team_id = line.workflow_team_ids[line.active_product_index + 1]
                if next_team_id in team_ids:
                    is_upcoming = True

            if is_current or is_upcoming:
                # Obje üzerine geçici olarak flag ekle
                line.is_upcoming_for_me = not is_current and is_upcoming
                my_lines.append(line)

        # Görev bazlı gruplandır
        task_map = {}
        for line in my_lines:
            task = line.task
            if task.id not in task_map:
                task_map[task.id] = {
                    'task_id': task.id,
                    'task_title': task.title,
                    'task_description': task.description,
                    'task_status': task.status,
                    'task_priority': task.priority,
                    'task_owner': task.owner.get_full_name() or task.owner.username,
                    'task_due_date': task.due_date.isoformat() if task.due_date else None,
                    'product_lines': [],
                }
            # Kalan miktar ve dinamik Miktar hesaplaması (Kanat/Panel x2 Sadece CNC, Giben, Laminasyon, Kanat için)
            displayed_quantity = line.quantity
            item_name = (line.model_code or "").lower()
            if "kanat" in item_name or "panel" in item_name:
                user_dept = (user.department or "").lower()
                target_teams = ["cnc", "giben", "laminasyon", "kanat"]
                if any(t in user_dept for t in target_teams):
                    displayed_quantity = line.quantity * 2

            remaining = max(0, displayed_quantity - line.qty_produced)
            task_map[task.id]['product_lines'].append({
                'id': line.id,
                'model_code': line.model_code,
                'variant': line.variant,
                'dimension': line.dimension,
                'color': line.color,
                'product_color_code': line.product_color_code,
                'brief_intro': line.brief_intro,
                'image_base64': line.image_base64,
                'unit_type': line.unit_type,
                'quantity': displayed_quantity,
                'qty_produced': line.qty_produced,
                'remaining': remaining,
                'fire_qty': line.fire_qty,
                'completion_rate': line.completion_rate,
                'workflow_team_ids': line.workflow_team_ids,
                'active_product_index': line.active_product_index,
                'stage_done': line.stage_done,
                'current_team_id': line.current_team_id,
                'is_upcoming': getattr(line, 'is_upcoming_for_me', False),
            })

        # Her görev için toplam ilerleme oranı hesapla
        result = []
        for task_data in task_map.values():
            lines = task_data['product_lines']
            if lines:
                total_target = sum(pl['quantity'] for pl in lines)
                total_produced = sum(pl['qty_produced'] for pl in lines)
                task_data['total_progress'] = round((total_produced / total_target) * 100, 1) if total_target > 0 else 0
                task_data['total_items'] = len(lines)
                task_data['total_remaining'] = sum(pl['remaining'] for pl in lines)
            result.append(task_data)

        return Response(result)


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

class CncReportView(APIView):
    """
    GET /api/tasks/reports/cnc-reports/
    CNC Ekiplerine ait günlük faaliyet raporlarını getirir.
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

        # CNC ekibi tarafından yapılan ve tamamlanmış veya o gün başlanmış kayıtlar
        # Filtre: Ekip adında CNC geçmeli ve ek bilgilerden en az biri dolu olmalı
        from django.db.models import Q
        qs = ProductLineHistory.objects.filter(
            team__name__icontains='CNC',
            started_at__date__lte=target_date
        ).exclude(
            completed_at__date__lt=target_date
        ).filter(
            Q(working_hours__isnull=False) | 
            ~Q(work_description='') | 
            ~Q(activity_notes='')
        ).select_related('product_line', 'product_line__task', 'worker')

        logs = []
        for h in qs:
            logs.append({
                'task_title': h.product_line.task.title,
                'model_code': h.product_line.model_code,
                'worker': h.worker.get_full_name() or h.worker.username if h.worker else '-',
                'working_hours': float(h.working_hours) if h.working_hours else 0,
                'work_description': h.work_description,
                'produced_qty': h.qty_produced_at_stage,
                'scrap_qty': h.scrap_qty_at_stage,
                'scrap_location': h.scrap_location,
                'activity_notes': h.activity_notes,
                'completed_at': h.completed_at,
            })

        return Response({
            'target_date': target_date.strftime('%Y-%m-%d'),
            'logs': logs
        })

class PvcReportView(APIView):
    """
    GET /api/tasks/reports/pvc-reports/
    PVC Dilimleme Ekiplerine ait günlük faaliyet raporlarını getirir.
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

        from django.db.models import Q
        qs = ProductLineHistory.objects.filter(
            team__name__icontains='PVC',
            started_at__date__lte=target_date
        ).exclude(
            completed_at__date__lt=target_date
        ).filter(
            ~Q(pvc_color='') | 
            ~Q(pvc_roll_size='') | 
            Q(pvc_meters__isnull=False) |
            ~Q(pvc_cut_size='')
        ).select_related('product_line', 'product_line__task', 'worker')

        logs = []
        for h in qs:
            logs.append({
                'task_title': h.product_line.task.title,
                'model_code': h.product_line.model_code,
                'worker': h.worker.get_full_name() or h.worker.username if h.worker else '-',
                'pvc_color': h.pvc_color,
                'pvc_roll_size': h.pvc_roll_size,
                'pvc_meters': float(h.pvc_meters) if h.pvc_meters else 0,
                'pvc_cut_size': h.pvc_cut_size,
                'produced_qty': h.qty_produced_at_stage,
                'scrap_qty': h.scrap_qty_at_stage,
                'activity_notes': h.activity_notes,
                'completed_at': h.completed_at,
            })

        return Response({
            'target_date': target_date.strftime('%Y-%m-%d'),
            'logs': logs
        })

class GibenReportView(APIView):
    """
    GET /api/tasks/reports/giben-reports/
    Giben Ekiplerine ait günlük faaliyet raporlarını getirir.
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

        from django.db.models import Q
        qs = ProductLineHistory.objects.filter(
            team__name__icontains='GIBEN',
            started_at__date__lte=target_date
        ).exclude(
            completed_at__date__lt=target_date
        ).filter(
            ~Q(giben_plate_size='') | 
            ~Q(work_description='')
        ).select_related('product_line', 'product_line__task', 'worker')

        logs = []
        for h in qs:
            logs.append({
                'task_title': h.product_line.task.title,
                'model_code': h.product_line.model_code,
                'worker': h.worker.get_full_name() or h.worker.username if h.worker else '-',
                'work_description': h.work_description,
                'giben_plate_size': h.giben_plate_size,
                'produced_qty': h.qty_produced_at_stage,
                'activity_notes': h.activity_notes,
                'completed_at': h.completed_at,
            })

        return Response({
            'target_date': target_date.strftime('%Y-%m-%d'),
            'logs': logs
        })


class TeamReportView(APIView):
    """
    GET /api/tasks/reports/team-reports/
    Dynamic activity report for any selected team_id on a given date.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        from .models import ProductLineHistory
        from django.utils import timezone
        import datetime
        from django.db.models import Q

        date_str = request.query_params.get('date')
        team_id = request.query_params.get('team_id')

        if not date_str:
            target_date = timezone.now().date()
        else:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()

        if not team_id:
            return Response({"detail": "team_id parametresi zorunludur."}, status=400)

        # Filter logs for selected team and target date
        qs = ProductLineHistory.objects.filter(
            team_id=team_id,
            started_at__date__lte=target_date
        ).exclude(
            completed_at__date__lt=target_date
        ).filter(
            Q(working_hours__isnull=False) |
            ~Q(work_description='') |
            ~Q(activity_notes='') |
            ~Q(pvc_color='') |
            ~Q(pvc_roll_size='') |
            Q(pvc_meters__isnull=False) |
            ~Q(pvc_cut_size='') |
            ~Q(giben_plate_size='')
        ).select_related('product_line', 'product_line__task', 'worker', 'team')

        logs = []
        for h in qs:
            logs.append({
                'task_title': h.product_line.task.title,
                'model_code': h.product_line.model_code,
                'worker': h.worker.get_full_name() or h.worker.username if h.worker else '-',
                'working_hours': float(h.working_hours) if h.working_hours else 0,
                'work_description': h.work_description,
                'scrap_location': h.scrap_location,
                'activity_notes': h.activity_notes,
                'produced_qty': h.qty_produced_at_stage,
                'scrap_qty': h.scrap_qty_at_stage,
                
                # PVC specific
                'pvc_color': h.pvc_color,
                'pvc_roll_size': h.pvc_roll_size,
                'pvc_meters': float(h.pvc_meters) if h.pvc_meters else 0,
                'pvc_cut_size': h.pvc_cut_size,

                # Giben specific
                'giben_plate_size': h.giben_plate_size,
                
                'completed_at': h.completed_at.strftime('%Y-%m-%d %H:%M:%S') if h.completed_at else None,
            })

        return Response({
            'target_date': target_date.strftime('%Y-%m-%d'),
            'logs': logs
        })

class SystemSettingsView(APIView):
    """
    GET /api/tasks/settings/
    PUT /api/tasks/settings/
    Mesai saatleri gibi sistem ayarlarını okur ve günceller.
    """
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        from .models import SystemSettings
        from .serializers import SystemSettingsSerializer
        settings = SystemSettings.get_settings()
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        from .models import SystemSettings
        from .serializers import SystemSettingsSerializer
        settings = SystemSettings.get_settings()
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

