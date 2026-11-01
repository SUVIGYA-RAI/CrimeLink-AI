"""
Cases app admin configuration.
"""

from django.contrib import admin
from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """Admin configuration for Case model."""
    list_display = ('case_number', 'title', 'case_type', 'status', 'priority', 'created_by', 'date_created')
    list_filter = ('status', 'priority', 'case_type')
    search_fields = ('case_number', 'title', 'description')
    readonly_fields = ('date_created', 'updated_at')
    ordering = ('-date_created',)
