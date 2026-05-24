from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from datetime import timedelta

from .models import StockItem, StockTransaction
from .serializers import (
    StockItemSerializer,
    StockItemListSerializer,
    StockTransactionSerializer,
    StockEntrySerializer,
    StockExitSerializer,
)
from accounts.permissions import IsAdminOrManager


class StockItemViewSet(viewsets.ModelViewSet):
    """
    /api/stock/items/ — Stok CRUD.
    Entry/Exit özel action'larla yapılır.
    """
    queryset = StockItem.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return StockItemListSerializer
        return StockItemSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManager()]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get('search'):
            qs = qs.filter(name__icontains=params['search'])
        if params.get('critical') == 'true':
            from django.db.models import F
            qs = qs.filter(current_quantity__lte=F('min_threshold'))
        return qs

    @action(detail=True, methods=['post'], url_path='entry')
    def stock_entry(self, request, pk=None):
        """POST /api/stock/items/{id}/entry/ — Stok giriş."""
        serializer = StockEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tx = StockTransaction.create_entry(
                stock_item_id=pk,
                quantity=serializer.validated_data['quantity'],
                user=request.user,
                notes=serializer.validated_data.get('notes', ''),
            )
            item = StockItem.objects.get(id=pk)
            return Response({
                'detail': f'Stok girişi başarılı. Yeni miktar: {item.current_quantity}',
                'transaction': StockTransactionSerializer(tx).data,
                'item': StockItemSerializer(item).data,
            })
        except StockItem.DoesNotExist:
            return Response(
                {'detail': 'Stok kalemi bulunamadı.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=['post'], url_path='exit')
    def stock_exit(self, request, pk=None):
        """POST /api/stock/items/{id}/exit/ — Stok çıkış (transaction-lock)."""
        serializer = StockExitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tx = StockTransaction.create_exit(
                stock_item_id=pk,
                quantity=serializer.validated_data['quantity'],
                user=request.user,
                notes=serializer.validated_data.get('notes', ''),
            )
            item = StockItem.objects.get(id=pk)
            return Response({
                'detail': f'Stok çıkışı başarılı. Kalan miktar: {item.current_quantity}',
                'transaction': StockTransactionSerializer(tx).data,
                'item': StockItemSerializer(item).data,
            })
        except StockItem.DoesNotExist:
            return Response(
                {'detail': 'Stok kalemi bulunamadı.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response(
                {'detail': str(e.message if hasattr(e, 'message') else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class StockHistoryView(APIView):
    """
    GET /api/stock/history/ — Giriş/Çıkış geçmişi tarih filtresiyle.
    Query params: start_date, end_date, transaction_type, stock_item
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = StockTransaction.objects.select_related(
            'stock_item', 'performed_by'
        ).all()

        start = request.query_params.get('start_date')
        end = request.query_params.get('end_date')
        tx_type = request.query_params.get('transaction_type')
        item_id = request.query_params.get('stock_item')

        if start:
            d = parse_date(start)
            if d:
                qs = qs.filter(created_at__date__gte=d)
        if end:
            d = parse_date(end)
            if d:
                qs = qs.filter(created_at__date__lte=d)
        if tx_type in ('entry', 'exit'):
            qs = qs.filter(transaction_type=tx_type)
        if item_id:
            qs = qs.filter(stock_item_id=item_id)

        qs = qs[:100]  # Son 100 kayıt
        serializer = StockTransactionSerializer(qs, many=True)
        return Response(serializer.data)


class StockDashboardView(APIView):
    """
    GET /api/stock/dashboard/ — Stok özet istatistikleri.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import F, Sum, Count
        from django.utils import timezone

        items = StockItem.objects.all()
        total_items = items.count()
        critical_items = items.filter(
            current_quantity__lte=F('min_threshold')
        ).count()
        out_of_stock = items.filter(current_quantity__lte=0).count()

        # Son 30 günün hareketleri
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_txs = StockTransaction.objects.filter(
            created_at__gte=thirty_days_ago
        )
        total_entries = recent_txs.filter(
            transaction_type='entry'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        total_exits = recent_txs.filter(
            transaction_type='exit'
        ).aggregate(total=Sum('quantity'))['total'] or 0

        def add_months(date_value, month_delta):
            year = date_value.year + ((date_value.month - 1 + month_delta) // 12)
            month = ((date_value.month - 1 + month_delta) % 12) + 1
            return date_value.replace(year=year, month=month, day=1)

        # Aylık tüketim (son 6 takvim ayı)
        monthly_consumption = []
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for i in range(5, -1, -1):
            month_start = add_months(current_month_start, -i)
            month_end = add_months(month_start, 1) if i > 0 else now
            exits = StockTransaction.objects.filter(
                transaction_type='exit',
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).aggregate(total=Sum('quantity'))['total'] or 0
            monthly_consumption.append({
                'month': month_start.strftime('%Y-%m'),
                'label': month_start.strftime('%b %Y'),
                'quantity': float(exits),
            })

        # Kritik stok uyarıları
        critical_list = StockItemListSerializer(
            items.filter(current_quantity__lte=F('min_threshold'))[:10],
            many=True,
        ).data

        return Response({
            'total_items': total_items,
            'critical_items': critical_items,
            'out_of_stock': out_of_stock,
            'entries_30d': float(total_entries),
            'exits_30d': float(total_exits),
            'monthly_consumption': monthly_consumption,
            'critical_stock_list': critical_list,
        })


class StockExportPDFView(APIView):
    """
    GET /api/stock/export-pdf/
    Son stok hareketlerini PDF olarak indirir.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = styles['Heading1']
        title_style.alignment = 1 # Center
        elements.append(Paragraph("MDF Stok Hareketleri Raporu", title_style))
        elements.append(Spacer(1, 20))

        # Data Query
        transactions = StockTransaction.objects.select_related(
            'stock_item', 'performed_by'
        ).order_by('-created_at')[:100]

        # Table Header
        data = [
            ["Tarih", "Tip", "Urun", "Miktar", "Kullanim Yeri", "Yapan Kisi"]
        ]

        for tx in transactions:
            date_str = tx.created_at.strftime("%Y-%m-%d %H:%M")
            tx_type = "Giris" if tx.transaction_type == 'entry' else "Cikis"
            item_name = tx.stock_item.name[:25] + "..." if len(tx.stock_item.name) > 25 else tx.stock_item.name
            qty_str = f"+{tx.quantity}" if tx.transaction_type == 'entry' else f"-{tx.quantity}"
            location = tx.usage_location or "-"
            person = tx.performed_by.username if tx.performed_by else "-"
            
            data.append([date_str, tx_type, item_name, qty_str, location, person])

        # Table Style
        t = Table(data, colWidths=[90, 45, 160, 50, 100, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f6ef7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
        ]))
        
        # Add dynamic row coloring for Entry/Exit
        for i in range(1, len(data)):
            if data[i][1] == "Giris":
                t.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#10b981'))])) # Green
            else:
                t.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), colors.HexColor('#ef4444'))])) # Red

        elements.append(t)
        doc.build(elements)

        pdf_value = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="stok_raporu.pdf"'
        response.write(pdf_value)
        return response

# Import here to avoid circular import
from .serializers import StockItemListSerializer
