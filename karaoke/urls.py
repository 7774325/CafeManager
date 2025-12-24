from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Management
    path('dashboard/', views.dashboard, name='dashboard'),
    path('summary/', views.daily_summary, name='daily_summary'),
    path('monitor/', views.karaoke_list, name='karaoke_monitor'),
    
    # Room & Session Management
    path('rooms/', views.karaoke_list, name='karaoke_list'),
    path('session/start/', views.start_session, name='start_session'),
    path('session/manage/<int:session_id>/', views.manage_session, name='manage_session'),
    path('session/checkout/<int:session_id>/', views.checkout_session, name='checkout_session'),
    
    # Kitchen & Ordering
    path('kitchen/', views.kitchen_view, name='kitchen_view'),
    path('kitchen/complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('kitchen/void/<int:order_id>/', views.void_order, name='void_order'), # NEW
    path('room-order/<int:session_id>/', views.add_to_room_order, name='add_to_room_order'),
    path('tablet-order/<int:session_id>/', views.customer_tablet_order, name='tablet_order'),
    
    # POS & Sales
    path('pos/', views.record_sale, name='record_sale'),
    path('submit-sale/', views.submit_sale, name='submit_sale'),
    path('sales-history/', views.sales_history, name='sales_history'),
    path('receipt/<int:transaction_id>/', views.receipt_detail, name='receipt_detail'),
    
    # Customers & Loyalty
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/history/<int:customer_id>/', views.customer_history, name='customer_history'),
    path('customers/pay-credit/<int:customer_id>/', views.pay_credit, name='pay_credit'),
    
    # Inventory & Tools
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    
    # Public Booking
    path('booking/', views.booking_landing, name='booking_landing'),
    path('welcome/', views.booking_landing, name='booking_welcome'),
    path('booking/submit/', views.submit_booking_request, name='submit_booking_request'),
    path('welcome/submit/', views.submit_booking_request, name='submit_booking_legacy'),
    path('booking/approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    
    # Live Bill API for Tablet
    path('api/session/<int:session_id>/bill/', views.get_session_bill, name='get_session_bill'),
]