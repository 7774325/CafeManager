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

class StockAdjustment(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='stock_adjustments', null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

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