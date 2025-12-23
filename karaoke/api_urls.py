# karaoke/api_urls.py

from django.urls import path
from . import views

urlpatterns = [
    # C1: Availability check
    #path('availability/', views.check_availability, name='api_availability_check'), 
    
    # M2: In-Room Order Placement 
    path('orders/place/', views.place_order, name='api_place_order'), 
    
    # S4: Staff Order Status Update 
    #path('orders/update_status/<int:order_id>/', views.update_order_status, name='api_update_status'), 
    
    # I3: Session Status/Bill check 
    #path('session/status/<int:booking_id>/', views.get_session_status, name='api_session_status'), 
    
    # B5/B6: Final Invoice Submission (POST to finalize bill)
    #path('checkout/finalize/<int:booking_id>/', views.finalize_invoice, name='api_finalize_invoice'), 
]