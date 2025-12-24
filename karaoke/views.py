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
from .models import RoomSession, BookingRequest, RoomOrder, RoomOrderItem, Room

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
    outlet = request.outlet  # Use middleware-provided outlet
    active_sessions = RoomSession.objects.filter(outlet=outlet, status__in=['Booked', 'Active', 'Paused'])
    bookings = BookingRequest.objects.filter(status='Pending').order_by('requested_date')
    
    # Get actual rooms from database
    actual_rooms = Room.objects.filter(outlet=outlet)
    rooms = []
    
    if not actual_rooms.exists():
        messages.warning(request, "No rooms found. Please create at least one Room in the Admin panel first.")
    
    for room in actual_rooms:
        room_data = {
            'id': room.id,
            'name': room.name,
            'type': room.room_type,
            'capacity': room.capacity,
            'status': room.status,
            'color': 'success' if room.status == 'Available' else 'danger',
            'price_per_hour': str(room.price_per_hour)
        }
        
        # Check if there's an active session in this room
        session = active_sessions.filter(room=room).first()
        if session:
            room_data.update({
                'status': 'Occupied',
                'color': 'danger',
                'session_id': session.id,
                'customer_name': session.customer_name,
                'order_total': session.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            })
        
        rooms.append(room_data)
    
    # Pass available rooms for the start session modal
    available_rooms = Room.objects.filter(outlet=outlet, status='Available')
    
    return render(request, 'karaoke/rooms.html', {
        'rooms': rooms, 
        'available_rooms': available_rooms,
        'bookings': bookings, 
        'currency': CURRENCY
    })

@login_required
def start_session(request):
    """Start a new karaoke session."""
    outlet = get_user_outlet(request.user)
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        customer_name = request.POST.get('customer_name')
        duration = int(request.POST.get('duration', 60))
        
        room = get_object_or_404(Room, id=room_id, outlet=outlet)
        room.status = 'Active'
        room.save()
        
        session = RoomSession.objects.create(
            outlet=outlet,
            room=room,
            customer_name=customer_name,
            booked_duration_minutes=duration,
            base_rate=room.get_hourly_rate(),
            status='Active',
            started_at=timezone.now()
        )
        return redirect('checkout_session', session_id=session.id)
    
    rooms = Room.objects.filter(outlet=outlet, status='Available')
    return render(request, 'karaoke/start_session.html', {'rooms': rooms})

@login_required
def checkout_session(request, session_id):
    """Checkout and close a karaoke session."""
    session = get_object_or_404(RoomSession, id=session_id)
    outlet = get_user_outlet(request.user)
    
    # Ensure outlet isolation
    if session.outlet != outlet:
        return redirect('karaoke_list')
    
    # Complete session and calculate charges
    session.complete_session()
    kitchen_total = session.orders.aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0')
    session.food_beverage_charge = Decimal(kitchen_total)
    session.recalculate_total()

    if request.method == 'POST':
        session.status = 'Completed'
        session.save()
        
        # Record payment
        SaleTransaction.objects.create(
            outlet=outlet, 
            customer=session.customer,
            total_amount=session.total_charge,
            payment_method=request.POST.get('payment_method', 'Cash'),
            customer_name=session.customer_name, 
            status='Completed'
        )
        
        # Mark room as available for cleaning
        session.room.status = 'Cleaning'
        session.room.save()
        
        return redirect('karaoke_list')

    return render(request, 'karaoke/checkout.html', {
        'session': session,
        'room_charge': session.room_charge,
        'extra_time_charge': session.extra_time_charge,
        'kitchen_total': session.food_beverage_charge,
        'grand_total': session.total_charge,
        'payment_methods': PAYMENT_METHODS,
        'currency': CURRENCY
    })

@login_required
def manage_session(request, session_id):
    """Manage active session - pause, add time, etc."""
    session = get_object_or_404(RoomSession, id=session_id)
    outlet = get_user_outlet(request.user)
    
    if session.outlet != outlet:
        return redirect('karaoke_list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'pause':
            session.pause_session()
        elif action == 'resume':
            session.resume_session()
        elif action == 'add_time':
            minutes = int(request.POST.get('minutes', 0))
            session.add_extra_time(minutes)
            session.save()
    
    return render(request, 'karaoke/manage_session.html', {
        'session': session,
        'elapsed_minutes': session.get_elapsed_minutes(),
        'currency': CURRENCY
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
    active_sessions = RoomSession.objects.filter(outlet=outlet, status__in=['Booked', 'Active', 'Paused'])
    bookings = BookingRequest.objects.filter(status='Pending').order_by('requested_date')
    
    # Get actual rooms from database
    actual_rooms = Room.objects.filter(outlet=outlet)
    rooms = []
    
    for room in actual_rooms:
        room_data = {
            'id': room.id,
            'name': room.name,
            'type': room.room_type,
            'capacity': room.capacity,
            'status': room.status,
            'color': 'success' if room.status == 'Available' else 'danger',
            'price_per_hour': str(room.price_per_hour)
        }
        
        # Check if there's an active session in this room
        session = active_sessions.filter(room=room).first()
        if session:
            room_data.update({
                'status': 'Occupied',
                'color': 'danger',
                'session_id': session.id,
                'customer_name': session.customer_name,
                'order_total': session.orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            })
        
        rooms.append(room_data)
    
    return render(request, 'karaoke/rooms.html', {'rooms': rooms, 'bookings': bookings})

@login_required
def start_session(request):
    outlet = get_user_outlet(request.user)
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id, outlet=outlet)
        duration = int(request.POST.get('duration', room.min_booking_duration))
        
        session = RoomSession.objects.create(
            room=room,
            outlet=outlet,
            customer_name=request.POST.get('customer_name', 'Guest'),
            booked_duration_minutes=duration,
            base_rate=room.get_hourly_rate(),
            status='Booked',
            started_at=timezone.now()
        )
        return redirect('checkout_session', session_id=session.id)
    
    rooms = Room.objects.filter(outlet=outlet, status='Available')
    return render(request, 'karaoke/start_session.html', {'rooms': rooms})

def customer_tablet_order(request, session_id):
    session = get_object_or_404(RoomSession, id=session_id, status__in=['Booked', 'Active', 'Paused'])
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
    rate = 150 if "VIP" in session.room.name else 100 
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

        session.status = 'Completed'
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