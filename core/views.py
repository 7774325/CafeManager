import csv
import json
import pandas as pd
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from core.models import Outlet, Product, SaleTransaction, SaleItem, Employee, Customer, CreditPayment

# --- HELPER UTILITIES ---
def get_user_outlet(user):
    try:
        # Check for employee profile
        return user.employee.outlet 
    except:
        return Outlet.objects.first()

# --- DASHBOARD ---
@login_required
def dashboard(request):
    outlet = get_user_outlet(request.user)
    # Using the date field we fixed in models
    sales_qs = SaleTransaction.objects.filter(outlet=outlet)
    total_sales = sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_items = Product.objects.filter(outlet=outlet).count()
    low_stock = Product.objects.filter(outlet=outlet, current_stock_level__lt=10).count()
    
    # Statistics for the dashboard
    categories_stats = Product.objects.filter(outlet=outlet).values('category').annotate(count=Count('id')).order_by('category')
    recent_sales = sales_qs.order_by('-date')[:5]

    return render(request, 'karaoke/dashboard.html', {
        'outlet': outlet, 
        'total_sales': total_sales, 
        'total_items': total_items,
        'low_stock_count': low_stock, 
        'categories': categories_stats,
        'recent_sales': recent_sales
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
    
    # SITA FIX: Get unique category list only
    categories = Product.objects.filter(outlet=outlet).values_list('category', flat=True).distinct().order_by('category')
    categories = [c for c in categories if c] # Remove empty categories
    
    favorites = products.filter(is_favorite=True)
    
    return render(request, 'core/pos.html', {
        'products': products,
        'categories': categories,
        'favorites': favorites
    })

@login_required
def submit_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            payment_method = data.get('payment_method')
            customer_name = data.get('customer_name')
            outlet = get_user_outlet(request.user)
            
            total_float = sum(float(item['price']) * int(item['quantity']) for item in cart)
            total_amount = Decimal(str(round(total_float, 2)))

            # Handle Customer Credit logic
            customer_obj = None
            if customer_name:
                customer_obj, created = Customer.objects.get_or_create(name=customer_name)
                if payment_method == 'Credit':
                    customer_obj.current_balance += total_amount
                    customer_obj.save()

            # Create Transaction (Matching our new Model fields)
            transaction = SaleTransaction.objects.create(
                outlet=outlet, 
                total_amount=total_amount, 
                payment_method=payment_method,
                customer_name=customer_name, # Saved as string in new model
                status='Completed'
            )

            for item in cart:
                product = Product.objects.get(id=item['id'])
                # SaleItem now uses 'sale' instead of 'transaction'
                SaleItem.objects.create(
                    sale=transaction, 
                    product=product, 
                    quantity=item['quantity'], 
                    price=Decimal(str(item['price'])) # price instead of unit_price
                )
                # Deduct Stock
                product.current_stock_level -= int(item['quantity'])
                product.save()

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
@login_required
def karaoke_list(request):
    rooms = [
        {'id': 1, 'name': 'VIP Room A', 'status': 'Available', 'color': 'success'},
        {'id': 2, 'name': 'Standard Room 1', 'status': 'Occupied', 'color': 'danger'},
    ]
    return render(request, 'karaoke/rooms.html', {'rooms': rooms})

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
def outlet_settings(request): return render(request, 'core/settings.html')