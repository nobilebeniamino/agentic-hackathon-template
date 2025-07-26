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
    list_display = ['received_at', 'ai_category', 'ai_severity', 'conversation_display', 
                   'conversation_status', 'location_display', 'processing_time_display', 
                   'is_critical', 'has_error']
    list_filter = ['ai_severity', 'ai_category', 'conversation_status', 'is_conversation_starter', 
                   'needs_follow_up', 'has_error', 'is_test_message', 'received_at']
    search_fields = ['user_message', 'ai_category', 'user_ip', 'follow_up_question']
    readonly_fields = ['received_at', 'processed_at', 'location_display', 'processing_time_display',
                      'conversation_display', 'follow_up_count']
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('User Input', {
            'fields': ('user_message', 'user_latitude', 'user_longitude', 'location_display')
        }),
        ('AI Response', {
            'fields': ('ai_category', 'ai_severity', 'ai_instructions', 'external_feed')
        }),
        ('Conversation', {
            'fields': ('parent_message', 'conversation_step', 'is_conversation_starter', 
                      'conversation_status', 'needs_follow_up', 'follow_up_question', 
                      'conversation_display', 'follow_up_count'),
            'classes': ('collapse',)
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
        return super().get_queryset(request).select_related('parent_message').prefetch_related('follow_ups')
    
    def conversation_display(self, obj):
        """Display conversation information in a readable format"""
        if obj.is_conversation_starter:
            follow_up_count = obj.follow_ups.count()
            if follow_up_count > 0:
                return f"🗣️ Starter (Step {obj.conversation_step}) → {follow_up_count} follow-ups"
            else:
                return f"🗣️ Starter (Step {obj.conversation_step})"
        else:
            return f"💬 Follow-up (Step {obj.conversation_step}) ← Parent: #{obj.parent_message.id if obj.parent_message else 'None'}"
    conversation_display.short_description = "Conversation"
    
    def follow_up_count(self, obj):
        """Count of follow-up messages"""
        return obj.follow_ups.count()
    follow_up_count.short_description = "Follow-ups Count"
    
    def mark_conversations_completed(self, request, queryset):
        """Mark selected conversations as completed"""
        updated = queryset.update(conversation_status='completed')
        self.message_user(request, f'{updated} conversations marked as completed.')
    mark_conversations_completed.short_description = "Mark conversations as completed"
    
    def mark_conversations_abandoned(self, request, queryset):
        """Mark selected conversations as abandoned"""
        updated = queryset.update(conversation_status='abandoned')
        self.message_user(request, f'{updated} conversations marked as abandoned.')
    mark_conversations_abandoned.short_description = "Mark conversations as abandoned"
    
    actions = ['mark_conversations_completed', 'mark_conversations_abandoned']
