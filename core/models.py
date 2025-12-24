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
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

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