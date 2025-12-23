# CafeManager - Enterprise Café & Karaoke Management System

## Overview
Multi-tenant, enterprise-grade platform for managing independent hospitality outlets. Designed as "Loyverse+" with deep karaoke integration, real-time POS, and automated HR/payroll.

## Multi-Tenant Architecture (Foundation)

### Data Isolation Strategy
Every record is tied to an `Outlet ID`. Staff at one outlet cannot see another outlet's data.

**Models with Outlet FK:**
- Employee, Product, SaleTransaction, Expense, Customer
- StockAdjustment, CreditPayment
- RoomSession, BookingRequest, RoomOrder, RoomOrderItem, Room

### Key Components

#### 1. Multi-Tenant Utilities (`core/multi_tenant.py`)
- **get_user_outlet()**: Gets the logged-in user's outlet
- **OutletQuerySet/OutletManager**: Custom managers for filtering
- **MultiTenantMixin**: View mixin for automatic outlet filtering
- **filter_queryset_for_user()**: Generic filtering function

#### 2. Outlet Middleware (`CafeManager/middleware.py`)
- Automatically attaches `request.outlet` to every authenticated request
- Accessible in all views via `request.outlet`

#### 3. Usage in Views
```python
# Views can use:
outlet = request.outlet  # From middleware
# OR
from core.multi_tenant import get_user_outlet
outlet = get_user_outlet(request.user)

# Filter querysets:
Product.objects.filter(outlet=outlet)
```

## Project Architecture
- **Framework**: Django 5.2 with Django REST Framework
- **ASGI Server**: Daphne (WebSocket support)
- **Real-Time**: Django Channels for live updates
- **Database**: SQLite (dev), PostgreSQL (production)
- **Language**: Python 3.11+

## Directory Structure
```
CafeManager/          # Project settings + middleware
  - middleware.py     # Multi-tenant outlet middleware
core/                 # Core POS, Finance, HR
  - multi_tenant.py   # Multi-tenant utilities
  - models.py         # Outlet, Employee, Product, Sale, Customer, etc.
  - views.py          # Views using outlet filtering
  - admin.py          # Admin with outlet filters
karaoke/              # Room management + orders
  - models.py         # Room, RoomSession, RoomOrder, etc.
  - consumers.py      # WebSocket consumers
  - routing.py        # WebSocket routing
templates/            # HTML templates
media/                # Product images
staticfiles/          # Static assets
```

## Running the Application
```bash
daphne -b 0.0.0.0 -p 5000 CafeManager.asgi:application
```

## Multi-Tenant Implementation Notes

### Adding New Models
When creating models that should be multi-tenant:
```python
class MyModel(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='my_models')
    # other fields...
```

### Filtering Data in Views
```python
@login_required
def my_view(request):
    outlet = request.outlet  # From middleware
    my_data = MyModel.objects.filter(outlet=outlet)
    return render(request, 'template.html', {'data': my_data})
```

### Database Migrations Applied
- Migration 0022 (core): Added outlet FK to Customer, StockAdjustment, CreditPayment
- Migration 0010 (karaoke): Added outlet FK to BookingRequest, RoomOrder, RoomOrderItem

## Recent Changes
- 2025-12-23: Multi-tenant foundation implemented
  - All models now tied to Outlet
  - Middleware for automatic request.outlet
  - Utility functions for filtering
  - Admin interface outlet filters configured

## TODO - Next Phases
1. **POS System** - Interactive product grid, live order cart, split billing
2. **Karaoke Module** - Session management, room lifecycle, tablet interface
3. **Inventory** - Real-time stock deduction, low stock alerts
4. **HR & Payroll** - Three payment types (P/C/D), attendance tracking
5. **Financial Reports** - P&L, expense auditing, outlet performance
