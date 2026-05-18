from django.contrib import admin
from .models import CustomUser, TeamAssociate


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(TeamAssociate)
class TeamAssociateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'department', 'is_active', 'created_at']
    list_filter = ['is_active', 'department']
    search_fields = ['full_name']
