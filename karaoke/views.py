import json
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from core.models import Outlet, Product, SaleTransaction, Customer, SaleItem
from .models import RoomSession, BookingRequest, RoomOrder, RoomOrderItem


import json
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from core.models import Outlet, Product, SaleTransaction, Customer, SaleItem
from .models import RoomSession, BookingRequest, RoomOrder, RoomOrderItem

# --- CONFIGURATION ---
PAYMENT_METHODS = ['Cash', 'Transfer', 'Card', 'Credit']
CURRENCY = "MVR"

def get_user_outlet(user):
    try:
        return user.employee.outlet 
    except:
        return Outlet.objects.first()

def notify_sita(subject, message):
    try:
        send_mail(subject, message, 'system@chillokay.com', ['sita@chillokay.com'], fail_silently=True)
    except:
        pass

# --- DASHBOARD ---
@login_required
def dashboard(request):
    outlet = get_user_outlet(request.user)
    today = timezone.now().date()
    today_sales = SaleTransaction.objects.filter(outlet=outlet, date__date=today)
    total_rev = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    hot_picks = RoomOrderItem.objects.filter(order__session__outlet=outlet).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
    low_stock_items = Product.objects.filter(outlet=outlet, current_stock_level__lt=10).count()
    categories = Product.objects.filter(outlet=outlet).values('category').annotate(item_count=Count('id')).order_by('category')

    return render(request, 'karaoke/dashboard.html', {
        'total_sales': total_rev,
        'total_products': Product.objects.filter(outlet=outlet).count(),
        'low_stock_count': low_stock_items,
        'hot_picks': hot_picks,
        'categories': categories,
        'pending_bookings_count': BookingRequest.objects.filter(status='Pending').count(),
        'currency': CURRENCY
    })

# --- ROOM SESSIONS ---
@login_required
def karaoke_list(request):
    outlet = get_user_outlet(request.user)
    active_sessions = RoomSession.objects.filter(outlet=outlet, is_active=True)
    bookings = BookingRequest.objects.filter(status='Pending').order_by('requested_date')
    
    rooms = [
        {'name': 'VIP Room A', 'status': 'Available', 'color': 'success'},
        {'name': 'Standard Room 1', 'status': 'Available', 'color': 'success'},
    ]
    
    for room in rooms:
        session = active_sessions.filter(room_name=room['name']).first()
        if session:
            room.update({
                'status': 'Occupied', 'color': 'danger', 'session_id': session.id,
                'customer_name': session.customer_name,
                'order_total': session.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            })
    return render(request, 'karaoke/rooms.html', {'rooms': rooms, 'bookings': bookings, 'currency': CURRENCY})

@login_required
def checkout_session(request, session_id):
    session = get_object_or_404(RoomSession, id=session_id)
    outlet = get_user_outlet(request.user)
    
    duration = (timezone.now() - session.start_time).total_seconds() / 3600
    hours = max(1, round(duration)) 
    rate = 150 if "VIP" in session.room_name else 100 
    room_charge = Decimal(hours * rate)
    kitchen_total = session.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    grand_total = room_charge + Decimal(kitchen_total)

    if request.method == 'POST':
        submitted_amount = Decimal(request.POST.get('final_amount', grand_total))
        SaleTransaction.objects.create(
            outlet=outlet, 
            total_amount=submitted_amount,
            payment_method=request.POST.get('payment_method'),
            customer_name=session.customer_name, 
            status='Completed'
        )
        session.is_active = False
        session.save()
        return redirect('karaoke_list')

    return render(request, 'karaoke/checkout.html', {
        'session': session, 'room_charge': room_charge,
        'kitchen_total': kitchen_total, 'grand_total': grand_total, 
        'payment_methods': PAYMENT_METHODS, 'currency': CURRENCY
    })

# --- SALES HISTORY (Fixing IDR to MVR) ---
@login_required
def sales_history(request):
    sales = SaleTransaction.objects.all().order_by('-date')
    return render(request, 'karaoke/sales_history.html', {
        'sales': sales,
        'currency': CURRENCY
    })

# --- DAILY SUMMARY ---
@login_required
def daily_summary(request):
    outlet = get_user_outlet(request.user)
    today = timezone.now().date()
    sales_today = SaleTransaction.objects.filter(outlet=outlet, date__date=today)
    
    total_revenue = sales_today.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    cash_total = sales_today.filter(payment_method='Cash').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    card_total = sales_today.filter(payment_method='Card').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    transfer_total = sales_today.filter(payment_method='Transfer').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    best_sellers = SaleItem.objects.filter(sale__date__date=today).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:10]

    return render(request, 'karaoke/summary.html', {
        'today': today,
        'total_revenue': total_revenue,
        'cash_total': cash_total,
        'card_total': card_total,
        'transfer_total': transfer_total,
        'best_sellers': best_sellers,
        'recent_sales': sales_today.order_by('-date')[:20],
        'currency': CURRENCY
    })

# --- POS ---
@login_required
def record_sale(request):
    outlet = get_user_outlet(request.user)
    return render(request, 'core/pos.html', {
        'products': Product.objects.filter(outlet=outlet),
        'customers': Customer.objects.all(),
        'payment_methods': PAYMENT_METHODS,
        'categories': Product.objects.filter(outlet=outlet).values_list('category', flat=True).distinct(),
        'currency': CURRENCY
    })

# ... (other views like start_session, kitchen_view etc. remain same as previous full file)

# --- CONFIGURATION ---
PAYMENT_METHODS = ['Cash', 'Transfer', 'Card']

def get_user_outlet(user):
    try:
        return user.employee.outlet 
    except:
        return Outlet.objects.first()

def notify_sita(subject, message):
    try:
        send_mail(subject, message, 'system@chillokay.com', ['sita@chillokay.com'], fail_silently=True)
    except:
        pass

# --- PUBLIC & BOOKING VIEWS ---
def booking_landing(request):
    return render(request, 'karaoke/booking_landing.html')

def submit_booking_request(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        BookingRequest.objects.create(
            customer_name=customer_name,
            phone_number=request.POST.get('phone_number'),
            requested_date=request.POST.get('requested_date'),
            requested_time=request.POST.get('requested_time'),
            duration_minutes=request.POST.get('duration')
        )
        notify_sita("New Booking!", f"{customer_name} submitted a request.")
        return render(request, 'karaoke/booking_success.html', {'name': customer_name})
    return redirect('booking_landing')

# --- DASHBOARD ---
@login_required
def dashboard(request):
    outlet = get_user_outlet(request.user)
    today = timezone.now().date()
    today_sales = SaleTransaction.objects.filter(outlet=outlet, date__date=today)
    total_rev = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    hot_picks = RoomOrderItem.objects.filter(order__session__outlet=outlet).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
    low_stock_items = Product.objects.filter(outlet=outlet, current_stock_level__lt=10).count()
    categories = Product.objects.filter(outlet=outlet).values('category').annotate(item_count=Count('id')).order_by('category')

    return render(request, 'karaoke/dashboard.html', {
        'total_sales': total_rev,
        'total_products': Product.objects.filter(outlet=outlet).count(),
        'low_stock_count': low_stock_items,
        'hot_picks': hot_picks,
        'categories': categories,
        'pending_bookings_count': BookingRequest.objects.filter(status='Pending').count()
    })

# --- ROOM SESSIONS & TABLET ORDERING ---
@login_required
def karaoke_list(request):
    outlet = get_user_outlet(request.user)
    active_sessions = RoomSession.objects.filter(outlet=outlet, is_active=True)
    bookings = BookingRequest.objects.filter(status='Pending').order_by('requested_date')
    
    rooms = [
        {'name': 'VIP Room A', 'status': 'Available', 'color': 'success'},
        {'name': 'Standard Room 1', 'status': 'Available', 'color': 'success'},
    ]
    
    for room in rooms:
        session = active_sessions.filter(room_name=room['name']).first()
        if session:
            room.update({
                'status': 'Occupied', 'color': 'danger', 'session_id': session.id,
                'customer_name': session.customer_name,
                'order_total': session.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            })
    return render(request, 'karaoke/rooms.html', {'rooms': rooms, 'bookings': bookings})

@login_required
def start_session(request):
    if request.method == 'POST':
        duration = int(request.POST.get('duration', 60))
        RoomSession.objects.create(
            room_name=request.POST.get('room_name'),
            customer_name=request.POST.get('customer_name', 'Guest'),
            end_time=timezone.now() + timedelta(minutes=duration),
            outlet=get_user_outlet(request.user),
            is_active=True
        )
    return redirect('karaoke_list')

def customer_tablet_order(request, session_id):
    session = get_object_or_404(RoomSession, id=session_id, is_active=True)
    products = Product.objects.filter(outlet=session.outlet).exclude(category='Room Rate')
    return render(request, 'karaoke/tablet_order.html', {'session': session, 'products': products})

@login_required
def add_to_room_order(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(RoomSession, id=session_id)
        data = json.loads(request.body)
        order = RoomOrder.objects.create(session=session)
        total = 0
        for item in data.get('items', []):
            prod = Product.objects.get(id=item['id'])
            qty = int(item['quantity'])
            RoomOrderItem.objects.create(order=order, product=prod, quantity=qty, price=prod.selling_price)
            total += (prod.selling_price * qty)
        order.total_price = total
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# NEW: Void function to handle customer cancellations
@login_required
def void_order(request, order_id):
    if not request.user.is_superuser:
        messages.error(request, "Only managers can void kitchen orders.")
        return redirect('kitchen_view')
        
    order = get_object_or_404(RoomOrder, id=order_id)
    # Simply delete the order so it leaves the kitchen view and the bill
    order.delete()
    messages.success(request, "Order was successfully voided.")
    return redirect('kitchen_view')

@login_required
def checkout_session(request, session_id):
    session = get_object_or_404(RoomSession, id=session_id)
    outlet = get_user_outlet(request.user)
    
    duration = (timezone.now() - session.start_time).total_seconds() / 3600
    hours = max(1, round(duration)) 
    rate = 150 if "VIP" in session.room_name else 100 
    room_charge = Decimal(hours * rate)
    kitchen_total = session.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    grand_total = room_charge + Decimal(kitchen_total)

    customer_record = Customer.objects.filter(name__iexact=session.customer_name).first()
    
    if request.method == 'POST':
        submitted_amount = Decimal(request.POST.get('final_amount', grand_total))
        if submitted_amount != grand_total and not request.user.is_superuser:
            messages.error(request, "Access Denied: Only managers can modify prices.")
            return redirect('checkout_session', session_id=session.id)

        SaleTransaction.objects.create(
            outlet=outlet, 
            customer=customer_record,
            total_amount=submitted_amount,
            payment_method=request.POST.get('payment_method'),
            customer_name=session.customer_name, 
            status='Completed'
        )

        if customer_record:
            customer_record.visit_count += 1
            customer_record.save()

        session.is_active = False
        session.save()
        messages.success(request, f"Bill settled: MVR {submitted_amount}")
        return redirect('karaoke_list')

    return render(request, 'karaoke/checkout.html', {
        'session': session, 'room_charge': room_charge,
        'kitchen_total': kitchen_total, 'grand_total': grand_total, 
        'payment_methods': PAYMENT_METHODS, 'currency': 'MVR'
    })

# --- POS & SALES ---
@login_required
def record_sale(request):
    outlet = get_user_outlet(request.user)
    return render(request, 'core/pos.html', {
        'products': Product.objects.filter(outlet=outlet),
        'customers': Customer.objects.all(),
        'payment_methods': PAYMENT_METHODS,
        'categories': Product.objects.filter(outlet=outlet).values_list('category', flat=True).distinct()
    })

@login_required
def submit_sale(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        outlet = get_user_outlet(request.user)
        customer_id = data.get('customer_id')
        customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
        
        transaction = SaleTransaction.objects.create(
            outlet=outlet,
            customer=customer,
            customer_name=data.get('customer_name', 'Walk-in'),
            table_number=data.get('table_number', 'Counter'),
            total_amount=Decimal(data.get('total_price')),
            payment_method=data.get('payment_method', 'Cash'),
            status='Completed'
        )
        
        for item in data.get('items', []):
            product = Product.objects.get(id=item['id'])
            SaleItem.objects.create(sale=transaction, product=product, quantity=item['quantity'], price=product.selling_price)
            product.current_stock_level -= int(item['quantity'])
            product.save()

        if customer:
            customer.visit_count += 1
            customer.save()

        return JsonResponse({'success': True, 'transaction_id': transaction.id})
    return JsonResponse({'success': False})

# --- DAILY SUMMARY ---
@login_required
def daily_summary(request):
    outlet = get_user_outlet(request.user)
    today = timezone.now().date()
    sales_today = SaleTransaction.objects.filter(outlet=outlet, date__date=today)
    
    total_revenue = sales_today.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    cash_total = sales_today.filter(payment_method='Cash').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    card_total = sales_today.filter(payment_method='Card').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    transfer_total = sales_today.filter(payment_method='Transfer').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    best_sellers = SaleItem.objects.filter(sale__date__date=today).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:10]

    return render(request, 'karaoke/summary.html', {
        'today': today,
        'total_revenue': total_revenue,
        'cash_total': cash_total,
        'card_total': card_total,
        'transfer_total': transfer_total,
        'best_sellers': best_sellers,
        'recent_sales': sales_today.order_by('-date')[:20]
    })

# --- KITCHEN & HISTORY ---
@login_required
def kitchen_view(request):
    pending_orders = RoomOrder.objects.filter(is_served=False).order_by('created_at')
    return render(request, 'karaoke/kitchen.html', {'orders': pending_orders})

@login_required
def complete_order(request, order_id):
    order = get_object_or_404(RoomOrder, id=order_id)
    order.is_served = True
    order.save()
    return redirect('kitchen_view')

@login_required
def sales_history(request):
    return render(request, 'karaoke/sales_history.html', {'sales': SaleTransaction.objects.all().order_by('-date')})

@login_required
def receipt_detail(request, transaction_id):
    sale = get_object_or_404(SaleTransaction, id=transaction_id)
    return render(request, 'karaoke/receipt.html', {'sale': sale})

@login_required
def customer_list(request):
    return render(request, 'karaoke/customers.html', {'customers': Customer.objects.all()})

@login_required
def customer_history(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    sales = SaleTransaction.objects.filter(customer=customer).order_by('-date')
    preferences = SaleItem.objects.filter(sale__customer=customer).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:10]
    return render(request, 'karaoke/customer_history.html', {'customer': customer, 'sales': sales, 'preferences': preferences})

@login_required
def low_stock_report(request):
    outlet = get_user_outlet(request.user)
    products = Product.objects.filter(outlet=outlet, current_stock_level__lt=10).order_by('current_stock_level')
    return render(request, 'karaoke/low_stock.html', {'products': products, 'threshold': 10})

@login_required
def toggle_favorite(request, product_id):
    p = get_object_or_404(Product, id=product_id)
    p.is_favorite = not p.is_favorite
    p.save()
    return JsonResponse({'success': True, 'is_favorite': p.is_favorite})