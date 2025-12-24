# CafeManager - Enterprise Café & Karaoke Management System

## Overview
Multi-tenant, enterprise-grade platform for managing independent hospitality outlets. Designed as "Loyverse+" with deep karaoke integration, real-time POS, and automated HR/payroll.

---

## PHASES COMPLETED

### Phase 1: Multi-Tenant Architecture ✅
**Every record tied to an Outlet ID - Complete data isolation**
- Outlet Middleware: `request.outlet` on every request
- Multi-Tenant Utilities: `get_user_outlet()`, `MultiTenantMixin`
- All core models have outlet FK

### Phase 2: POS System ✅
**Interactive product grid, real-time cart, checkout with stock deduction**
- Product grid (filtered by outlet)
- Real-time cart with quantity controls
- Payment methods: Cash, Card, Transfer, Credit
- Real-time stock deduction on checkout
- Customer visit count & credit tracking
- **Endpoints**: `/pos/`, `/api/pos/submit/`

### Phase 3: Karaoke Module Backend ✅
**Complete session lifecycle with duration-based billing**
- Room model: Status lifecycle (Available → Booked → Active → Cleaning)
- RoomSession model: Complete session tracking with billing
- Billing formula: `(actual_minutes + extra_minutes) / 60 × hourly_rate`
- Session control: Pause/resume, add extra time
- **Views**: `start_session`, `manage_session`, `checkout_session`

### Phase 4: Inventory Management ✅
**Real-time stock tracking with low-stock alerts**

#### **InventoryLog Model**
- Action types: Sale, Purchase, Adjustment, Spoilage, Transfer
- Tracks: quantity_changed, previous_level, new_level
- Fields: reference (Transaction ID), notes, created_at
- Indexed by: outlet + created_at, product + created_at
- Read-only fields in admin: created_at, previous_level, new_level

#### **Real-Time Stock Deduction**
When a product is sold via POS:
```python
# 1. Stock deducted from Product.current_stock_level
# 2. InventoryLog entry created with transaction reference
# 3. Previous and new levels recorded
# 4. User attribution (sold by username)
```

#### **Low Stock Dashboard** 
`GET /stock/low/` - Professional, clean interface with:
- **Statistics Cards**:
  - Total Products in outlet
  - Low Stock Count
  - Critical Stock (< 5 units)
  - Out of Stock (≤ 0 units)
- **Adjustable Threshold**: Default 10 units, user-configurable
- **Low Stock Products Table**: Sorted by lowest level first
- **Recent Activity Log**: Last 20 inventory changes
- **Styling**: Lavender (#8b5cf6) & black gradient with professional typography

#### **UI Features**
- Gradient header with shadow
- Responsive grid layout (4-column on desktop, 1-column on mobile)
- Color-coded stock badges: Critical (red), Low (orange), Out (pink)
- Hover effects on cards and table rows
- Clean typography with proper spacing
- Auto-refresh ready for WebSockets

#### **Database Migration**
- Migration 0023: Created InventoryLog, deleted StockAdjustment
- Admin interface: InventoryLogAdmin with full filtering and search

---

## Key Database Models

```
Outlet (1) ────────→ (∞) Product
        ├─────────→ (∞) SaleTransaction
        ├─────────→ (∞) InventoryLog
        ├─────────→ (∞) RoomSession
        └─────────→ (∞) Customer

Product (1) ────────→ (∞) InventoryLog
SaleTransaction (1) ─→ (∞) SaleItem
                   └──→ Product (via SaleItem)
```

---

## API Routes

### POS
| Route | Method | Purpose |
|-------|--------|---------|
| `/pos/` | GET | POS interface |
| `/api/pos/submit/` | POST | Checkout & create transaction + logs |

### Inventory
| Route | Method | Purpose |
|-------|--------|---------|
| `/stock/low/` | GET | Low stock dashboard |
| `/stock/bulk/` | GET | Bulk stock entry |

### Karaoke
| Route | Method | Purpose |
|-------|--------|---------|
| `/karaoke/session/start/` | POST | Create new session |
| `/karaoke/session/manage/<id>/` | POST | Pause/resume/add time |
| `/karaoke/session/checkout/<id>/` | POST | Finalize & payment |

---

## Technology Stack
- **Framework**: Django 5.2 + REST Framework
- **Server**: Daphne (ASGI, WebSocket-ready)
- **Database**: SQLite (dev), PostgreSQL (production)
- **Frontend**: Bootstrap 5 + vanilla JS
- **UI**: Lavender & black gradient design

---

## Recent Changes (2025-12-24)

**Phase 4: Inventory Management**
- Created InventoryLog model (action, quantity_changed, previous_level, new_level)
- Updated POS checkout to log all stock deductions with transaction reference
- Built low-stock dashboard with modern UI (lavender/black gradient)
- Added configurable threshold (default 10 units)
- Implemented responsive layout with stats cards and activity log
- Admin interface with filtering by action, outlet, date
- Database migration 0023 applied successfully

---

## Next Phases

1. **Karaoke Frontend** (Priority)
   - Real-time session dashboard with progress bars
   - Tablet ordering interface
   - Staff session management

2. **Multi-Outlet Inventory**
   - Stock transfers between outlets
   - Consolidated reporting

3. **HR & Payroll** (Complex)
   - Three payment types: P (Fixed), C (Hourly), D (Daily)
   - GPS attendance tracking

4. **Financial Intelligence**
   - P&L reports
   - Outlet performance dashboards
