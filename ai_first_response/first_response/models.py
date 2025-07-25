from django.db import models
from django.utils import timezone

class EmergencyCategory(models.Model):
    """Model for emergency category quick actions"""
    title = models.CharField(max_length=100, help_text="Display name for the emergency category")
    quick_message = models.TextField(help_text="Pre-filled message when user clicks this category")
    icon = models.CharField(max_length=10, help_text="Emoji icon for the category")
    css_class = models.CharField(max_length=50, default="btn-outline-danger", 
                                help_text="Bootstrap CSS class for the button")
    is_active = models.BooleanField(default=True, help_text="Whether to show this category")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Emergency Category"
        verbose_name_plural = "Emergency Categories"
        ordering = ['order', 'title']
    
    def __str__(self):
        return f"{self.icon} {self.title}"


class ReceivedMessage(models.Model):
    """Model to store received emergency messages and responses"""
    
    # Message type choices
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text Message'),
        ('voice', 'Voice Message'),
    ]
    
    # Severity choices
    SEVERITY_CHOICES = [
        ('CRIT', 'Critical'),
        ('HIGH', 'High'),
        ('MED', 'Medium'),
        ('LOW', 'Low'),
        ('INFO', 'Information'),
    ]
    
    # Message details
    message_text = models.TextField(help_text="Message content (original or transcribed)")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text', help_text="Type of message")
    language = models.CharField(max_length=10, default='en', help_text="Language of the message")
    
    # Original user input (backward compatibility)
    user_message = models.TextField(help_text="Original message from user")
    user_latitude = models.FloatField(help_text="User's latitude coordinate")
    user_longitude = models.FloatField(help_text="User's longitude coordinate")
    
    # AI Response
    ai_category = models.CharField(max_length=100, blank=True, help_text="AI classified category")
    ai_severity = models.CharField(max_length=4, choices=SEVERITY_CHOICES, blank=True, 
                                  help_text="AI classified severity level")
    ai_instructions = models.JSONField(default=list, help_text="AI generated instructions")
    
    # Context data
    external_feed = models.TextField(blank=True, help_text="External data feed used for context")
    response_time_ms = models.PositiveIntegerField(null=True, blank=True, 
                                                  help_text="Response time in milliseconds")
    
    # Metadata
    user_ip = models.GenericIPAddressField(null=True, blank=True, help_text="User's IP address")
    user_agent = models.TextField(blank=True, help_text="User's browser user agent")
    session_key = models.CharField(max_length=40, blank=True, help_text="User's session key")
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True, help_text="When message was received")
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When AI finished processing")
    
    # Status flags
    is_test_message = models.BooleanField(default=False, help_text="Mark as test/demo message")
    has_error = models.BooleanField(default=False, help_text="Whether processing had errors")
    error_message = models.TextField(blank=True, help_text="Error details if any")
    
    class Meta:
        verbose_name = "Received Message"
        verbose_name_plural = "Received Messages"
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['received_at']),
            models.Index(fields=['ai_severity']),
            models.Index(fields=['ai_category']),
            models.Index(fields=['user_latitude', 'user_longitude']),
        ]
    
    def __str__(self):
        return f"{self.ai_category or 'Unknown'} - {self.user_message[:50]}... ({self.received_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def location_display(self):
        """Format coordinates for display"""
        return f"{self.user_latitude:.4f}, {self.user_longitude:.4f}"
    
    @property
    def is_critical(self):
        """Check if this is a critical emergency"""
        return self.ai_severity in ['CRIT', 'HIGH']
    
    @property
    def processing_time_display(self):
        """Display processing time in human readable format"""
        if self.response_time_ms is None:
            return "Unknown"
        if self.response_time_ms < 1000:
            return f"{self.response_time_ms}ms"
        else:
            return f"{self.response_time_ms/1000:.1f}s"
