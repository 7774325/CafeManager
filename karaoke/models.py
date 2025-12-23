from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.models import Outlet, Product, Customer

# --- ROOM MANAGEMENT MODELS ---

class Room(models.Model):
    """Physical karaoke room with capacity and pricing."""
    ROOM_TYPES = [
        ('VIP', 'VIP Room'),
        ('Standard', 'Standard Room'),
    ]
    
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Booked', 'Booked'),
        ('Active', 'Active'),
        ('Cleaning', 'Cleaning'),
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='karaoke_rooms')
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='Standard')
    capacity = models.IntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    
    # Pricing
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=100, help_text="Base hourly rate")
    price_per_minute = models.DecimalField(max_digits=10, decimal_places=2, default=2, help_text="Rate for partial minutes")
    
    # Configuration
    min_booking_duration = models.IntegerField(default=60, help_text="Minimum duration in minutes")

    def __str__(self):
        return f"{self.name} ({self.room_type})"

    class Meta:
        ordering = ['name']
        unique_together = ('outlet', 'name')

    def get_hourly_rate(self):
        """Get the hourly rate based on room type."""
        return self.price_per_hour or (Decimal('150') if self.room_type == 'VIP' else Decimal('100'))


class RoomSession(models.Model):
    """Active karaoke session in a room - tracks time and billing."""
    STATUS_CHOICES = [
        ('Booked', 'Booked'),
        ('Active', 'Active'),
        ('Paused', 'Paused'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='karaoke_sessions', null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='sessions')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Session Timing
    booked_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True, help_text="When session actually started")
    paused_at = models.DateTimeField(null=True, blank=True, help_text="When session was paused")
    ended_at = models.DateTimeField(null=True, blank=True, help_text="When session was ended/closed")
    
    # Duration & Billing
    booked_duration_minutes = models.IntegerField(default=60)
    actual_duration_minutes = models.IntegerField(default=0)
    total_pause_minutes = models.IntegerField(default=0)
    extra_time_minutes = models.IntegerField(default=0)
    
    # Rates & Charges
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    room_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_time_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    food_beverage_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Booked')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.room.name} - {self.customer_name or 'Guest'} ({self.status})"

    class Meta:
        ordering = ['-started_at']

    def get_elapsed_minutes(self):
        """Get minutes elapsed since session started (excluding pauses)."""
        if not self.started_at:
            return 0
        end_time = self.ended_at or timezone.now()
        elapsed = (end_time - self.started_at).total_seconds() / 60
        return int(elapsed) - self.total_pause_minutes

    def calculate_room_charge(self):
        """Calculate room charge based on duration."""
        if not self.started_at:
            return Decimal('0')
        minutes = self.get_elapsed_minutes() + self.extra_time_minutes
        if minutes < 1:
            return Decimal('0')
        hours = Decimal(minutes) / Decimal('60')
        rate = self.base_rate or self.room.get_hourly_rate()
        return (hours * rate).quantize(Decimal('0.00'))

    def calculate_extra_time_charge(self):
        """Separate charge for extra time if applicable."""
        if self.extra_time_minutes <= 0:
            return Decimal('0')
        hours = Decimal(self.extra_time_minutes) / Decimal('60')
        rate = self.base_rate or self.room.get_hourly_rate()
        return (hours * rate).quantize(Decimal('0.00'))

    def recalculate_total(self):
        """Recalculate all charges and update total."""
        self.room_charge = self.calculate_room_charge()
        self.extra_time_charge = self.calculate_extra_time_charge()
        self.total_charge = (
            self.room_charge + self.extra_time_charge + self.food_beverage_charge
        ).quantize(Decimal('0.00'))
        return self.total_charge

    def add_extra_time(self, minutes):
        """Add extra time to session."""
        if minutes > 0:
            self.extra_time_minutes += minutes
            self.recalculate_total()

    def pause_session(self):
        """Pause the session."""
        if self.status == 'Active' and not self.paused_at:
            self.paused_at = timezone.now()
            self.status = 'Paused'
            self.save()

    def resume_session(self):
        """Resume a paused session."""
        if self.status == 'Paused' and self.paused_at:
            pause_duration = int((timezone.now() - self.paused_at).total_seconds() / 60)
            self.total_pause_minutes += pause_duration
            self.paused_at = None
            self.status = 'Active'
            self.save()

    def complete_session(self):
        """Complete the session and finalize charges."""
        if self.status in ('Active', 'Paused'):
            self.ended_at = timezone.now()
            self.status = 'Completed'
            self.actual_duration_minutes = self.get_elapsed_minutes() + self.extra_time_minutes
            self.recalculate_total()
            self.save()


# Alias for compatibility
KaraokeSession = RoomSession

class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'), 
        ('Approved', 'Approved'), 
        ('Cancelled', 'Cancelled')
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='booking_requests', null=True)
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
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='room_orders', null=True)
    session = models.ForeignKey(RoomSession, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_served = models.BooleanField(default=False)

    def __str__(self):
        return f"Order for {self.session.room_name} at {self.created_at}"

class RoomOrderItem(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='room_order_items', null=True)
    order = models.ForeignKey(RoomOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

# --- EXISTING UTILITY MODELS ---

# Room model moved to top of file for better organization

class OutletSetting(models.Model):
    outlet = models.OneToOneField(Outlet, on_delete=models.CASCADE)
    notification_email = models.EmailField(blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Settings for {self.outlet.name}"
    
    