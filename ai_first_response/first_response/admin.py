from django.contrib import admin
from .models import EmergencyCategory, ReceivedMessage

@admin.register(EmergencyCategory)
class EmergencyCategoryAdmin(admin.ModelAdmin):
    list_display = ['icon', 'title', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'quick_message']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'title']
    
    fieldsets = (
        ('Category Details', {
            'fields': ('title', 'quick_message', 'icon')
        }),
        ('Display Settings', {
            'fields': ('css_class', 'is_active', 'order')
        }),
    )

@admin.register(ReceivedMessage)
class ReceivedMessageAdmin(admin.ModelAdmin):
    list_display = ['received_at', 'ai_category', 'ai_severity', 'location_display', 
                   'processing_time_display', 'is_critical', 'has_error']
    list_filter = ['ai_severity', 'ai_category', 'has_error', 'is_test_message', 'received_at']
    search_fields = ['user_message', 'ai_category', 'user_ip']
    readonly_fields = ['received_at', 'processed_at', 'location_display', 'processing_time_display']
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('User Input', {
            'fields': ('user_message', 'user_latitude', 'user_longitude', 'location_display')
        }),
        ('AI Response', {
            'fields': ('ai_category', 'ai_severity', 'ai_instructions', 'external_feed')
        }),
        ('Performance', {
            'fields': ('response_time_ms', 'processing_time_display', 'processed_at')
        }),
        ('Session Info', {
            'fields': ('user_ip', 'user_agent', 'session_key'),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('received_at', 'is_test_message', 'has_error', 'error_message')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
