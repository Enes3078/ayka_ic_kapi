from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockItemViewSet, StockHistoryView, StockDashboardView, StockExportPDFView

router = DefaultRouter()
router.register(r'items', StockItemViewSet, basename='stockitem')

urlpatterns = [
    path('history/', StockHistoryView.as_view(), name='stock-history'),
    path('dashboard/', StockDashboardView.as_view(), name='stock-dashboard'),
    path('export-pdf/', StockExportPDFView.as_view(), name='stock-export-pdf'),
    path('', include(router.urls)),
]
