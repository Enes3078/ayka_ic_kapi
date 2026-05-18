from django.contrib import admin
from .models import StockItem, StockTransaction


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'current_quantity', 'min_threshold', 'unit', 'updated_at']
    list_filter = ['unit']
    search_fields = ['sku', 'name']
    readonly_fields = ['sku']


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['stock_item', 'transaction_type', 'quantity', 'performed_by', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['stock_item__name', 'notes']
