from django.contrib import admin
from .models import RoomSession

@admin.register(RoomSession)
class RoomSessionAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'customer_name', 'start_time', 'end_time', 'is_active', 'outlet')
    list_filter = ('is_active', 'room_type', 'outlet')
    search_fields = ('room_name', 'customer_name')
    ordering = ('-start_time',)