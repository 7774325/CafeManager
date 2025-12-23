from django.contrib import admin
from .models import Room, RoomSession, BookingRequest, RoomOrder, RoomOrderItem

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'capacity', 'status', 'price_per_hour', 'outlet')
    list_filter = ('status', 'room_type', 'outlet')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(RoomSession)
class RoomSessionAdmin(admin.ModelAdmin):
    list_display = ('room', 'customer_name', 'status', 'started_at', 'total_charge', 'outlet')
    list_filter = ('status', 'outlet')
    search_fields = ('customer_name', 'room__name')
    ordering = ('-started_at',)
    readonly_fields = ('booked_at', 'room_charge', 'total_charge')

@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'requested_date', 'status', 'outlet')
    list_filter = ('status', 'requested_date', 'outlet')
    search_fields = ('customer_name', 'phone_number')

@admin.register(RoomOrder)
class RoomOrderAdmin(admin.ModelAdmin):
    list_display = ('session', 'created_at', 'total_price', 'is_served', 'outlet')
    list_filter = ('is_served', 'created_at', 'outlet')
    ordering = ('-created_at',)

@admin.register(RoomOrderItem)
class RoomOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('outlet',)