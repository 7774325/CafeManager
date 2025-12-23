from django.db import models
from django.utils import timezone
from core.models import Outlet, Product, Customer

# --- ROOM MANAGEMENT MODELS ---

class RoomSession(models.Model):
    ROOM_TYPES = [
        ('VIP', 'VIP Room'),
        ('Standard', 'Standard Room'),
    ]
    
    room_name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='Standard')
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.room_name} - {self.customer_name}"

class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'), 
        ('Approved', 'Approved'), 
        ('Cancelled', 'Cancelled')
    ]
    
    customer_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True)
    requested_date = models.DateField()
    requested_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking: {self.customer_name} on {self.requested_date}"

# --- NEW: KITCHEN/BAR ORDER MODELS ---

class RoomOrder(models.Model):
    session = models.ForeignKey(RoomSession, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_served = models.BooleanField(default=False)

    def __str__(self):
        return f"Order for {self.session.room_name} at {self.created_at}"

class RoomOrderItem(models.Model):
    order = models.ForeignKey(RoomOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

# --- EXISTING UTILITY MODELS ---

class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=4)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class OutletSetting(models.Model):
    outlet = models.OneToOneField(Outlet, on_delete=models.CASCADE)
    notification_email = models.EmailField(blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Settings for {self.outlet.name}"
    
    