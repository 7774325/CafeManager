"""
Multi-Tenant Utilities for CafeManager
Provides managers, querysets, and utilities for outlet-based data isolation
"""
from django.db import models
from django.db.models import Q


class OutletQuerySet(models.QuerySet):
    """Custom QuerySet that filters by outlet"""
    def for_outlet(self, outlet):
        """Filter queryset for a specific outlet"""
        if outlet:
            return self.filter(outlet=outlet)
        return self


class OutletManager(models.Manager):
    """Custom Manager for outlet-based filtering"""
    def get_queryset(self):
        return OutletQuerySet(self.model, using=self._db)
    
    def for_outlet(self, outlet):
        """Filter for a specific outlet"""
        return self.get_queryset().for_outlet(outlet)


def get_user_outlet(user):
    """
    Get the outlet for a given user.
    - If user is an employee, return their outlet
    - If user is staff/owner, return their first outlet
    - Otherwise return None
    """
    try:
        if hasattr(user, 'employee') and user.employee:
            return user.employee.outlet
    except:
        pass
    
    try:
        if hasattr(user, 'outlets') and user.outlets.exists():
            return user.outlets.first()
    except:
        pass
    
    return None


def filter_queryset_for_user(queryset, user, outlet_field='outlet'):
    """
    Generic function to filter any queryset by user's outlet
    
    Args:
        queryset: Django QuerySet to filter
        user: User object
        outlet_field: Field name that references Outlet (default='outlet')
    
    Returns:
        Filtered QuerySet
    """
    outlet = get_user_outlet(user)
    if outlet:
        filter_kwargs = {outlet_field: outlet}
        return queryset.filter(**filter_kwargs)
    return queryset.none()


class MultiTenantMixin:
    """
    Mixin for views to enforce multi-tenant outlet filtering.
    Automatically filters querysets by user's outlet.
    """
    def get_outlet(self):
        """Get the user's outlet"""
        return get_user_outlet(self.request.user)
    
    def get_queryset(self):
        """Override get_queryset to filter by outlet"""
        qs = super().get_queryset()
        outlet = self.get_outlet()
        if outlet and 'outlet' in [f.name for f in qs.model._meta.get_fields()]:
            return qs.filter(outlet=outlet)
        return qs.none() if outlet else qs
