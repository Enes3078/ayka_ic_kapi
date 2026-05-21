from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet, TeamViewSet, ExcelImportView, 
    WorkerTrackingView, ProductLineViewSet, MyTeamQueueView,
    ReportingDashboardView, WorkerDetailAPIView, MyPastTasksView, ProductViewSet,
    TaskReportView, ProductionReportView, WorkflowTemplateViewSet, CncReportView,
    PvcReportView, GibenReportView, TeamReportView, SystemSettingsView
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
    path('reports/cnc-reports/', CncReportView.as_view(), name='cnc-reports'),
    path('reports/pvc-reports/', PvcReportView.as_view(), name='pvc-reports'),
    path('reports/giben-reports/', GibenReportView.as_view(), name='giben-reports'),
    path('reports/team-reports/', TeamReportView.as_view(), name='team-reports'),
    path('settings/', SystemSettingsView.as_view(), name='settings'),
    path('', include(router.urls)),
]


