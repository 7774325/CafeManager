# CafeManager - Enterprise Café & Karaoke Management System

## Overview
Multi-tenant, enterprise-grade platform for managing independent hospitality outlets. Designed as "Loyverse+" with deep karaoke integration, real-time POS, and automated HR/payroll.

## PHASES COMPLETED

### Phase 1: Multi-Tenant Architecture ✅
**Every record tied to an Outlet ID - Complete data isolation**

**Models with Outlet FK:**
- Employee, Product, SaleTransaction, Expense, Customer
- StockAdjustment, CreditPayment, RoomSession, BookingRequest
- RoomOrder, RoomOrderItem, Room

**Core Components:**
- **Multi-Tenant Utilities** (`core/multi_tenant.py`): get_user_outlet(), OutletQuerySet, MultiTenantMixin
- **Outlet Middleware** (`CafeManager/middleware.py`): Attaches request.outlet to every request
- **Automatic Filtering**: All views use `request.outlet` or `get_user_outlet()`

---

### Phase 2: POS System ✅
**Interactive product grid, live cart, checkout with real-time stock deduction**

**Features:**
- Interactive product grid (filtered by outlet)
- Real-time order cart with quantity controls
- Customer selection (outlet-specific customers)
- Payment methods: Cash, Card, Transfer, Credit
- Real-time stock deduction on checkout
- Customer visit count tracking
- Customer credit balance updates

**Key Endpoint:**
```
POST /api/pos/submit/
{
    "customer_id": int|null,
    "table_number": string,
    "payment_method": "Cash|Card|Transfer|Credit",
    "items": [
        {"id": product_id, "name": name, "price": price, "quantity": qty}
    ]
}
```

**Views:**
- `GET /pos/` - POS Interface (shows outlet-specific products & customers)
- `POST /api/pos/submit/` - Checkout (creates SaleTransaction & deducts stock)

---

## Project Architecture
- **Framework**: Django 5.2 + Django REST Framework
- **ASGI Server**: Daphne (WebSocket support)
- **Real-Time**: Django Channels for live updates
- **Database**: SQLite (dev), PostgreSQL (production)
- **Language**: Python 3.11+

---

## Directory Structure
```
CafeManager/              # Project settings + middleware
  - middleware.py         # Multi-tenant outlet middleware
core/                     # POS, Finance, HR
  - multi_tenant.py       # Multi-tenant utilities
  - models.py             # Outlet, Employee, Product, Sale, etc.
  - views.py              # Views with outlet filtering
  - admin.py              # Admin with outlet filters
  - urls.py               # POS routes
  - templates/core/pos.html
karaoke/                  # Room management + orders
  - models.py             # Room, RoomSession, RoomOrder, etc.
  - consumers.py          # WebSocket consumers
  - routing.py            # WebSocket routing
templates/                # HTML templates
media/                    # Product images
staticfiles/              # Static assets
```

---

## How to Use (Quick Start)

### Multi-Tenant Filtering
```python
# All views automatically use request.outlet:
outlet = request.outlet

# Filter data:
Product.objects.filter(outlet=outlet)

# Or use helper:
from core.multi_tenant import get_user_outlet
outlet = get_user_outlet(request.user)
```

### POS System
1. Navigate to `/pos/`
2. Select customer (optional)
3. Click products to add to cart
4. Select payment method
5. Click "SUBMIT & PRINT"
6. SaleTransaction created with outlet isolation

---

## Database Migrations Applied
- Migration 0022 (core): outlet FK on Customer, StockAdjustment, CreditPayment
- Migration 0010 (karaoke): outlet FK on BookingRequest, RoomOrder, RoomOrderItem

---

## TODO - Next Phases

1. **Karaoke Module** (Priority)
   - Session management (Available → Booked → Active → Cleaning)
   - Room lifecycle tracking
   - Tablet interface for in-room orders
   - Session monitoring with real-time progress
   - Extra time management

2. **Inventory Intelligence**
   - Low stock alert reports
   - Predictive stock deduction validation
   - Multi-outlet stock transfers

3. **HR & Payroll** (Complex)
   - Three payment types: P (Fixed), C (Hourly), D (Daily)
   - Attendance tracking (clock-in/out with GPS tagging)
   - Automated payroll calculations

4. **Financial Intelligence**
   - P&L summary reports (Revenue - Expenses)
   - Expense auditing with receipt uploads
   - Outlet performance comparison
   - Daily/Weekly/Monthly summaries

5. **Kitchen Display System**
   - Real-time order push via WebSockets
   - Order status tracking
   - Integrate with cart checkout

---

## Recent Changes
- 2025-12-23: Multi-tenant foundation + POS system implemented
  - All models tied to Outlet
  - Middleware for automatic request.outlet
  - Interactive POS with cart and checkout
  - Real-time stock deduction
