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
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            request.outlet = get_user_outlet(request.user)
        else:
            request.outlet = None
        return None
