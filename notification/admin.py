from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "notification_type", "is_read", "created_at")
    list_filter = ("is_read", "notification_type", "created_at")
    search_fields = ("title", "message", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

