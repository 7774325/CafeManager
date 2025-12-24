from django.db import models
from django.contrib.auth.models import User

# --- BASIC INFRASTRUCTURE ---

class Outlet(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outlets')
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Employee(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('P', 'Permanent (Fixed Monthly)'),
        ('C', 'Commission-Based'),
        ('D', 'Daily-Rated'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='employees')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Payment Structure
    payment_type = models.CharField(max_length=1, choices=PAYMENT_TYPE_CHOICES, default='P')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="For Permanent: Monthly salary, For Commission: Min salary, For Daily: Daily rate")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Commission % for commission-based employees")
    
    # Employment Details
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(null=True, blank=True)
    
    # Legacy field for backward compatibility
    @property
    def salary(self):
        return self.base_salary
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"
    
    class Meta:
        ordering = ['name']
        unique_together = ('outlet', 'user')

# --- PRODUCT & INVENTORY ---

class Product(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='products', null=True)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, null=True, blank=True) 
    category = models.CharField(max_length=100, blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock_level = models.IntegerField(default=0)
    is_favorite = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category if self.category else 'No Category'})"

class InventoryLog(models.Model):
    """Log all inventory changes - purchases, sales, adjustments, etc."""
    ACTION_CHOICES = [
        ('Sale', 'Sale'),
        ('Purchase', 'Purchase'),
        ('Adjustment', 'Adjustment'),
        ('Spoilage', 'Spoilage'),
        ('Transfer', 'Transfer'),
    ]
    
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='inventory_logs', null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='Sale')
    quantity_changed = models.IntegerField(help_text="Positive for additions, negative for deductions")
    previous_level = models.IntegerField(default=0)
    new_level = models.IntegerField(default=0)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Transaction ID, PO number, etc.")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} ({self.action}: {self.quantity_changed})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['outlet', 'created_at']),
            models.Index(fields=['product', 'created_at']),
        ]


# Legacy alias for backward compatibility
StockAdjustment = InventoryLog

# --- SALES & CUSTOMERS ---

class Customer(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='customers', null=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    total_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # NEW LOYALTY FIELDS
    visit_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.visit_count} visits)"

class SaleTransaction(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='sales', null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True) 
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Cash')
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='Completed')

    def __str__(self):
        return f"Transaction #{self.id} - {self.total_amount}"

class SaleItem(models.Model):
    sale = models.ForeignKey(SaleTransaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class CreditPayment(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='credit_payments', null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

# --- EXPENSES ---

class Expense(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.description

# --- HR & PAYROLL ---

class Attendance(models.Model):
    """Track employee check-in/check-out times."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(help_text="Date of attendance")
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Calculated hours worked")
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.employee.name} - {self.date}"
    
    class Meta:
        ordering = ['-date']
        unique_together = ('employee', 'date')
        indexes = [
            models.Index(fields=['outlet', 'date']),
            models.Index(fields=['employee', 'date']),
        ]
    
    def calculate_hours_worked(self):
        """Calculate hours worked based on check-in/check-out times."""
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, timedelta
            check_in = datetime.combine(datetime.today(), self.check_in_time)
            check_out = datetime.combine(datetime.today(), self.check_out_time)
            if check_out < check_in:
                check_out += timedelta(days=1)
            hours = (check_out - check_in).total_seconds() / 3600
            self.hours_worked = round(hours, 2)
        return self.hours_worked


class Payroll(models.Model):
    """Monthly payroll calculation for employees."""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Calculated', 'Calculated'),
        ('Approved', 'Approved'),
        ('Paid', 'Paid'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='payrolls')
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    # Calculations
    total_hours_worked = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions (future feature)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    calculated_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.employee.name} - {self.year}-{self.month:02d}"
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ('employee', 'year', 'month')
        indexes = [
            models.Index(fields=['outlet', 'year', 'month']),
        ]
    
    def calculate_payroll(self):
        """Calculate payroll based on employee payment type and attendance."""
        from django.db.models import Sum
        from decimal import Decimal
        from datetime import date
        
        # Get attendance for the month
        attendances = Attendance.objects.filter(
            employee=self.employee,
            outlet=self.outlet,
            date__year=self.year,
            date__month=self.month
        )
        
        total_hours = attendances.aggregate(Sum('hours_worked'))['hours_worked__sum'] or Decimal('0')
        self.total_hours_worked = total_hours
        
        # Calculate based on payment type
        if self.employee.payment_type == 'P':  # Permanent
            self.base_amount = self.employee.base_salary
            self.commission_amount = Decimal('0')
        elif self.employee.payment_type == 'D':  # Daily-Rated
            daily_rate = self.employee.base_salary
            working_days = attendances.count()
            self.base_amount = daily_rate * Decimal(working_days)
            self.commission_amount = Decimal('0')
        elif self.employee.payment_type == 'C':  # Commission-Based
            # Base amount = minimum salary
            self.base_amount = self.employee.base_salary
            # Commission = commission_rate % of outlet sales for the month
            sales = SaleTransaction.objects.filter(
                outlet=self.outlet,
                date__year=self.year,
                date__month=self.month
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
            self.commission_amount = (sales * self.employee.commission_rate / Decimal('100'))
        
        # Calculate net pay
        self.total_earnings = self.base_amount + self.commission_amount
        self.net_pay = self.total_earnings - self.deductions
        self.status = 'Calculated'
        self.save()
        return self.net_pay