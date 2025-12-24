from django.contrib import admin
from .models import Outlet, Employee, Product, SaleTransaction, SaleItem, Expense, InventoryLog, Customer, CreditPayment, Attendance, Payroll

@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location')
    list_display_links = ('id', 'name')
    fields = ('name', 'owner', 'location', 'logo')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'outlet', 'role', 'payment_type', 'base_salary', 'is_active')
    list_filter = ('outlet', 'payment_type', 'is_active')
    search_fields = ('name', 'phone', 'email')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'selling_price', 'current_stock_level', 'outlet')
    list_filter = ('outlet', 'category')
    search_fields = ('name', 'sku')

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'outlet', 'total_amount', 'payment_method', 'status')
    list_filter = ('outlet', 'status', 'payment_method')
    inlines = [SaleItemInline]

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'outlet')
    list_filter = ('outlet', 'date')

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'quantity_changed', 'created_at', 'outlet')
    list_filter = ('outlet', 'action', 'created_at')
    search_fields = ('product__name', 'reference')
    readonly_fields = ('created_at', 'previous_level', 'new_level')

# --- NEW: CUSTOMER & CREDIT ADMIN ---

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'current_balance', 'outlet')
    list_filter = ('outlet',)
    search_fields = ('name', 'phone')

@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount_paid', 'date', 'outlet')
    list_filter = ('outlet', 'customer', 'date')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'outlet', 'date', 'check_in_time', 'check_out_time', 'hours_worked')
    list_filter = ('outlet', 'date')
    search_fields = ('employee__name',)
    ordering = ['-date']

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'outlet', 'year', 'month', 'total_earnings', 'net_pay', 'status')
    list_filter = ('outlet', 'status', 'year', 'month')
    search_fields = ('employee__name',)
    readonly_fields = ('total_hours_worked', 'base_amount', 'commission_amount', 'total_earnings', 'calculated_at')