import csv
import json
import pandas as pd
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from core.models import Outlet, Product, SaleTransaction, SaleItem, Employee, Customer, CreditPayment, InventoryLog, Attendance, Payroll
from datetime import datetime, timedelta, date
from django.utils import timezone

# --- HELPER UTILITIES ---
def get_user_outlet(user):
    try:
        # Check for employee profile
        return user.employee.outlet 
    except:
        return Outlet.objects.first()

# --- DASHBOARD ---
def homepage(request):
    """Landing page for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing_page.html')

@login_required
def dashboard(request):
    outlet = get_user_outlet(request.user)
    today = date.today()
    
    # POS Sales today
    pos_sales = SaleTransaction.objects.filter(outlet=outlet, date__date=today)
    total_pos_sales = pos_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    
    # Karaoke Revenue today (completed sessions only)
    from karaoke.models import RoomSession
    karaoke_sessions = RoomSession.objects.filter(outlet=outlet, status='Completed', ended_at__date=today)
    total_karaoke_revenue = karaoke_sessions.aggregate(Sum('total_charge'))['total_charge__sum'] or Decimal('0')
    
    # Total Revenue
    total_revenue = total_pos_sales + total_karaoke_revenue
    
    # Low Stock Items
    low_stock_items = Product.objects.filter(outlet=outlet, current_stock_level__lt=10).order_by('current_stock_level')[:5]
    
    return render(request, 'core/manager_dashboard.html', {
        'outlet': outlet,
        'total_pos_sales': total_pos_sales,
        'total_karaoke_revenue': total_karaoke_revenue,
        'total_revenue': total_revenue,
        'low_stock_items': low_stock_items,
        'today': today,
        'now': timezone.now()
    })

# --- SALES HISTORY ---
@login_required
def sales_history(request):
    outlet = get_user_outlet(request.user)
    sales = SaleTransaction.objects.filter(outlet=outlet).order_by('-date')
    return render(request, 'karaoke/sales_history.html', {'sales': sales})

# --- CUSTOMER CREDIT ---
@login_required
def customer_credit_list(request):
    customers = Customer.objects.filter(current_balance__gt=0).order_by('-current_balance')
    return render(request, 'core/customer_credit.html', {'customers': customers})

@login_required
def clear_partial_credit(request, customer_id):
    if request.method == 'POST':
        amount_str = request.POST.get('amount', '0')
        amount = Decimal(amount_str) if amount_str else Decimal('0')
        customer = get_object_or_404(Customer, id=customer_id)
        if amount > 0:
            CreditPayment.objects.create(customer=customer, amount_paid=amount, notes="Partial payment received")
            customer.current_balance -= amount
            customer.save()
            messages.success(request, f"MVR {amount} recorded for {customer.name}.")
    return redirect('customer_credit_list')

# --- DATA MANAGEMENT (IMPORT/EXPORT) ---
@login_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        outlet = get_user_outlet(request.user)
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            for _, row in df.iterrows():
                name = row.get('Name')
                if pd.isna(name): continue
                Product.objects.update_or_create(
                    name=name, outlet=outlet,
                    defaults={
                        'sku': row.get('SKU'),
                        'category': str(row.get('Category')) if pd.notna(row.get('Category')) else "General",
                        'cost_price': float(row.get('Cost', 0)) if pd.notna(row.get('Cost')) else 0.0,
                        'selling_price': float(row.get('Price [Chillo]', 0)) if pd.notna(row.get('Price [Chillo]')) else 0.0,
                        'current_stock_level': int(float(row.get('In stock [Chillo]', 0))) if pd.notna(row.get('In stock [Chillo]')) else 0,
                    }
                )
            messages.success(request, "Import successful!")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return redirect('dashboard')
    return render(request, 'core/import_export.html')

@login_required
def export_data(request):
    outlet = get_user_outlet(request.user)
    products = Product.objects.filter(outlet=outlet)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{outlet.name}_inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'SKU', 'Category', 'Cost Price', 'Selling Price', 'In Stock'])
    for p in products:
        writer.writerow([p.name, p.sku, p.category, p.cost_price, p.selling_price, p.current_stock_level])
    return response

# --- POS SYSTEM ---
@login_required
def record_sale(request):
    outlet = get_user_outlet(request.user)
    products = Product.objects.filter(outlet=outlet).order_by('name')
    customers = Customer.objects.filter(outlet=outlet).order_by('name')
    
    # Get unique category list only
    categories = Product.objects.filter(outlet=outlet).values_list('category', flat=True).distinct().order_by('category')
    categories = [c for c in categories if c]
    
    favorites = products.filter(is_favorite=True)
    
    # Get rooms for this outlet (dynamic, not hardcoded)
    from karaoke.models import Room
    rooms = Room.objects.filter(outlet=outlet)
    
    return render(request, 'core/pos.html', {
        'products': products,
        'customers': customers,
        'categories': categories,
        'favorites': favorites,
        'outlet': outlet,
        'rooms': rooms
    })

@login_required
def submit_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('items', [])
            payment_method = data.get('payment_method', 'Cash')
            customer_id = data.get('customer_id')
            table_number = data.get('table_number', 'Counter')
            outlet = get_user_outlet(request.user)
            
            if not cart:
                return JsonResponse({'success': False, 'error': 'Cart is empty'}, status=400)
            
            total_float = sum(float(item['price']) * int(item['quantity']) for item in cart)
            total_amount = Decimal(str(round(total_float, 2)))

            # Get or create customer (filtered by outlet)
            customer_obj = None
            customer_name = None
            if customer_id:
                try:
                    customer_obj = Customer.objects.get(id=customer_id, outlet=outlet)
                    customer_name = customer_obj.name
                except Customer.DoesNotExist:
                    pass
            
            if not customer_name:
                customer_name = table_number or "Walk-in"

            # Create Transaction (Matching our new Model fields)
            transaction = SaleTransaction.objects.create(
                outlet=outlet, 
                customer=customer_obj,
                total_amount=total_amount, 
                payment_method=payment_method,
                customer_name=customer_name,
                status='Completed'
            )

            # Create Sale Items and deduct stock
            for item in cart:
                try:
                    product = Product.objects.get(id=item['id'], outlet=outlet)
                    qty = int(item['quantity'])
                    
                    SaleItem.objects.create(
                        sale=transaction, 
                        product=product, 
                        quantity=qty, 
                        price=Decimal(str(item['price']))
                    )
                    
                    # Log inventory deduction
                    previous_level = product.current_stock_level
                    product.current_stock_level -= qty
                    product.save()
                    
                    # Create inventory log
                    InventoryLog.objects.create(
                        outlet=outlet,
                        product=product,
                        action='Sale',
                        quantity_changed=-qty,
                        previous_level=previous_level,
                        new_level=product.current_stock_level,
                        reference=f"Transaction #{transaction.id}",
                        notes=f"Sold by {request.user.username}"
                    )
                except Product.DoesNotExist:
                    continue

            # Update customer visit count and balance if applicable
            if customer_obj:
                customer_obj.visit_count += 1
                if payment_method == 'Credit':
                    customer_obj.current_balance += total_amount
                customer_obj.save()

            return JsonResponse({'success': True, 'transaction_id': transaction.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_favorite = not product.is_favorite
    product.save()
    return JsonResponse({'success': True, 'is_favorite': product.is_favorite})

@login_required
def receipt_detail(request, transaction_id):
    sale = get_object_or_404(SaleTransaction, id=transaction_id)
    return render(request, 'karaoke/receipt.html', {'sale': sale})

# --- KARAOKE & TOOLS ---
# Note: karaoke_list is in karaoke/views.py - removed duplicate

@login_required
def bulk_stock_entry(request): return render(request, 'core/bulk_stock.html')
@login_required
def log_spoilage(request): return render(request, 'core/log_spoilage.html')
@login_required
def financial_summary_report(request): return render(request, 'core/financial_summary.html')
@login_required
def add_expense(request): return render(request, 'core/add_expense.html')
@login_required
def payroll_report(request): return render(request, 'core/payroll_report.html')
@login_required
def low_stock_report(request):
    """Display low stock alert dashboard for manager."""
    outlet = get_user_outlet(request.user)
    threshold = int(request.GET.get('threshold', 10))
    
    # Get low stock products
    low_stock_products = Product.objects.filter(
        outlet=outlet,
        current_stock_level__lt=threshold
    ).order_by('current_stock_level')
    
    # Get recent inventory logs for these products
    recent_logs = InventoryLog.objects.filter(
        outlet=outlet,
        product__in=low_stock_products
    ).order_by('-created_at')[:20]
    
    stats = {
        'total_products': Product.objects.filter(outlet=outlet).count(),
        'low_stock_count': low_stock_products.count(),
        'critical_stock': Product.objects.filter(outlet=outlet, current_stock_level__lt=5).count(),
        'out_of_stock': Product.objects.filter(outlet=outlet, current_stock_level__lte=0).count(),
    }
    
    return render(request, 'core/low_stock_report.html', {
        'low_stock_products': low_stock_products,
        'recent_logs': recent_logs,
        'stats': stats,
        'threshold': threshold,
        'outlet': outlet
    })

@login_required
def attendance_check_in(request):
    """Employee check-in."""
    outlet = get_user_outlet(request.user)
    employee = Employee.objects.filter(user=request.user, outlet=outlet).first()
    
    if not employee:
        messages.error(request, "No employee profile found")
        return redirect('dashboard')
    
    today = date.today()
    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        outlet=outlet,
        date=today
    )
    
    if not attendance.check_in_time:
        attendance.check_in_time = timezone.now().time()
        attendance.save()
        messages.success(request, f"Checked in at {attendance.check_in_time.strftime('%H:%M')}")
    else:
        messages.info(request, "Already checked in today")
    
    return redirect('dashboard')

@login_required
def attendance_check_out(request):
    """Employee check-out."""
    outlet = get_user_outlet(request.user)
    employee = Employee.objects.filter(user=request.user, outlet=outlet).first()
    
    if not employee:
        messages.error(request, "No employee profile found")
        return redirect('dashboard')
    
    today = date.today()
    try:
        attendance = Attendance.objects.get(employee=employee, outlet=outlet, date=today)
        if not attendance.check_out_time:
            attendance.check_out_time = timezone.now().time()
            attendance.calculate_hours_worked()
            attendance.save()
            messages.success(request, f"Checked out at {attendance.check_out_time.strftime('%H:%M')} - {attendance.hours_worked} hours worked")
        else:
            messages.info(request, "Already checked out today")
    except Attendance.DoesNotExist:
        messages.error(request, "No check-in record found for today")
    
    return redirect('dashboard')

@login_required
def attendance_report(request):
    """View attendance for the outlet."""
    outlet = get_user_outlet(request.user)
    month = request.GET.get('month', date.today().month)
    year = request.GET.get('year', date.today().year)
    
    try:
        month = int(month)
        year = int(year)
    except:
        month = date.today().month
        year = date.today().year
    
    attendances = Attendance.objects.filter(
        outlet=outlet,
        date__year=year,
        date__month=month
    ).order_by('employee__name', '-date')
    
    employees = Employee.objects.filter(outlet=outlet, is_active=True)
    
    return render(request, 'core/attendance_report.html', {
        'attendances': attendances,
        'employees': employees,
        'month': month,
        'year': year,
        'outlet': outlet
    })

@login_required
def payroll_calculate(request):
    """Calculate payroll for a month."""
    outlet = get_user_outlet(request.user)
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    
    employees = Employee.objects.filter(outlet=outlet, is_active=True)
    
    for employee in employees:
        payroll, created = Payroll.objects.get_or_create(
            employee=employee,
            outlet=outlet,
            year=year,
            month=month
        )
        payroll.calculate_payroll()
    
    messages.success(request, f"Payroll calculated for {year}-{month:02d}")
    return redirect('payroll_report', year=year, month=month)

@login_required
def payroll_report(request):
    """View payroll for the outlet."""
    outlet = get_user_outlet(request.user)
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    
    payrolls = Payroll.objects.filter(
        outlet=outlet,
        year=year,
        month=month
    ).order_by('employee__name')
    
    total_payroll = payrolls.aggregate(Sum('net_pay'))['net_pay__sum'] or Decimal('0')
    
    return render(request, 'core/payroll_report.html', {
        'payrolls': payrolls,
        'total_payroll': total_payroll,
        'month': month,
        'year': year,
        'outlet': outlet
    })

@login_required
def outlet_settings(request): return render(request, 'core/settings.html')