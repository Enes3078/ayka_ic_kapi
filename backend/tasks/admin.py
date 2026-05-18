from django.contrib import admin
from .models import Task, ProductLine, Team


class ProductLineInline(admin.TabularInline):
    model = ProductLine
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'created_at']
    filter_horizontal = ['members', 'associates']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'owner', 'team', 'created_at']
    list_filter = ['status', 'priority', 'team']
    search_fields = ['title', 'description']
    inlines = [ProductLineInline]


@admin.register(ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    list_display = ['model_code', 'quantity', 'qty_produced', 'fire_qty', 'task']
    list_filter = ['planning_mode']
