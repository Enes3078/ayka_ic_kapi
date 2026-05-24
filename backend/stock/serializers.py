from rest_framework import serializers
from decimal import Decimal
from .models import StockItem, StockTransaction


class StockTransactionSerializer(serializers.ModelSerializer):
    """Stok hareketi serializer — history listesi için."""
    performed_by_name = serializers.SerializerMethodField()
    stock_item_name = serializers.SerializerMethodField()

    class Meta:
        model = StockTransaction
        fields = [
            'id', 'stock_item', 'stock_item_name',
            'transaction_type', 'quantity',
            'performed_by', 'performed_by_name',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'performed_by', 'created_at']

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return obj.performed_by.get_full_name() or obj.performed_by.username
        return None

    def get_stock_item_name(self, obj):
        return obj.stock_item.name if obj.stock_item else None


class StockItemSerializer(serializers.ModelSerializer):
    """Stok kalemi serializer."""
    is_critical = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()
    recent_transactions = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            'id', 'sku', 'name', 'description', 'unit',
            'current_quantity', 'min_threshold',
            'is_critical', 'stock_status',
            'recent_transactions',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'sku', 'created_at', 'updated_at']

    def get_recent_transactions(self, obj):
        txs = obj.transactions.all()[:5]
        return StockTransactionSerializer(txs, many=True).data


class StockItemListSerializer(serializers.ModelSerializer):
    """Stok listesi için hafif serializer."""
    is_critical = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = StockItem
        fields = [
            'id', 'sku', 'name', 'unit',
            'current_quantity', 'min_threshold',
            'is_critical', 'stock_status',
            'updated_at',
        ]


class StockEntrySerializer(serializers.Serializer):
    """Stok giriş formu."""
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    notes = serializers.CharField(required=False, default='', allow_blank=True)


class StockExitSerializer(serializers.Serializer):
    """Stok çıkış formu."""
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    notes = serializers.CharField(required=False, default='', allow_blank=True)


class StockHistoryFilterSerializer(serializers.Serializer):
    """Stok geçmişi tarih filtresi."""
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    transaction_type = serializers.ChoiceField(
        choices=[('entry', 'Giriş'), ('exit', 'Çıkış')],
        required=False,
    )
    stock_item = serializers.IntegerField(required=False)
