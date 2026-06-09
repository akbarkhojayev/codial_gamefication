from django.contrib import admin
from .models import QueryLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'query_type', 'result_count', 'created_at']
    list_filter = ['query_type', 'created_at', 'user']
    search_fields = ['question', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Query', {
            'fields': ('question', 'query_type', 'result_count')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

