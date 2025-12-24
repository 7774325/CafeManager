"""
Multi-Tenant Middleware for CafeManager
Attaches the user's outlet to each request for convenient access
"""
from django.utils.deprecation import MiddlewareMixin
from core.multi_tenant import get_user_outlet


class OutletMiddleware(MiddlewareMixin):
    """
    Middleware that attaches the user's outlet to the request object.
    Allows views to access request.outlet directly.
    
    For superusers: defaults to the first outlet with data, or first outlet overall.
    For regular users: uses their employee's outlet.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                # Superusers can access all outlets - default to the first available
                from core.models import Outlet
                from karaoke.models import Room
                
                # Try to find outlet with rooms first
                outlet_with_rooms = Outlet.objects.filter(karaoke_rooms__isnull=False).first()
                if outlet_with_rooms:
                    request.outlet = outlet_with_rooms
                else:
                    # Fall back to first outlet
                    request.outlet = Outlet.objects.first()
            else:
                request.outlet = get_user_outlet(request.user)
        else:
            request.outlet = None
        return None
