from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, TeamViewSet, ExcelImportView, 
    WorkerTrackingView, ProductLineViewSet, MyTeamQueueView,
    ReportingDashboardView, WorkerDetailAPIView, MyPastTasksView, ProductViewSet,
    TaskReportView, ProductionReportView, WorkflowTemplateViewSet
)

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'workflow-templates', WorkflowTemplateViewSet, basename='workflowtemplate')
router.register(r'product-lines', ProductLineViewSet, basename='productline')

urlpatterns = [
    path('import-excel/', ExcelImportView.as_view(), name='import-excel'),
    path('worker-tracking/', WorkerTrackingView.as_view(), name='worker-tracking'),
    path('worker-tracking/<int:pk>/', WorkerDetailAPIView.as_view(), name='worker-detail'),
    path('my-team-queue/', MyTeamQueueView.as_view(), name='my-team-queue'),
    path('my-past-tasks/', MyPastTasksView.as_view(), name='my-past-tasks'),
    path('dashboard-stats/', ReportingDashboardView.as_view(), name='dashboard-stats'),
    path('reports/task-report/', TaskReportView.as_view(), name='task-report'),
    path('reports/production-report/', ProductionReportView.as_view(), name='production-report'),
    path('', include(router.urls)),
]


