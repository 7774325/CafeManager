# CafeManager - Enterprise Café & Karaoke Management System

## Overview
Multi-tenant, enterprise-grade platform for managing independent hospitality outlets. Designed as "Loyverse+" with deep karaoke integration, real-time POS, and automated HR/payroll.

## PHASES COMPLETED

### Phase 1: Multi-Tenant Architecture ✅
**Every record tied to an Outlet ID - Complete data isolation**

- Outlet Middleware (`CafeManager/middleware.py`): `request.outlet` on every request
- Multi-Tenant Utilities: `get_user_outlet()`, `MultiTenantMixin`
- All core models have outlet FK: Employee, Product, SaleTransaction, Customer, etc.

---

### Phase 2: POS System ✅
**Interactive product grid, live cart, checkout with real-time stock deduction**

- Product grid (filtered by outlet)
- Real-time cart with quantity controls
- Customer selection (outlet-specific)
- Payment methods: Cash, Card, Transfer, Credit
- Real-time stock deduction on checkout
- Customer visit count & credit tracking

**Endpoints:**
- `GET /pos/` - POS Interface
- `POST /api/pos/submit/` - Checkout

---

### Phase 3: Karaoke Module Backend ✅
**Complete karaoke session lifecycle with duration-based billing**

#### **Room Model**
```
- Multi-tenant (outlet FK)
- Status: Available → Booked → Active → Cleaning
- Types: VIP, Standard
- Pricing: price_per_hour, price_per_minute (configurable)
- Capacity tracking
```

#### **RoomSession Model** (Karaoke Session)
**Complete session tracking:**
```
Session Lifecycle:
  Booked → Active → Paused → Completed
  
Timing Fields:
  - booked_at: When session was booked
  - started_at: When customer actually started using room
  - paused_at: When session was paused (if applicable)
  - ended_at: When session was finalized
  
Duration Tracking:
  - booked_duration_minutes: Originally booked time
  - actual_duration_minutes: Time actually used
  - total_pause_minutes: Time paused (excluded from billing)
  - extra_time_minutes: Additional time added mid-session
  
Billing Fields:
  - base_rate: Hourly rate at session start (defaults to room rate)
  - room_charge: Base charge (calculated)
  - extra_time_charge: Extra time premium (calculated)
  - food_beverage_charge: F&B from RoomOrder items
  - total_charge: Grand total (calculated)
```

#### **Billing Calculation (Per Spec)**
```python
# Formula for room charge:
room_charge = (actual_minutes + extra_minutes) / 60 * hourly_rate

# Example:
# 90 minutes session at 100/hour = 1.5 * 100 = 150
# + 30 minutes extra = 0.5 * 100 = 50 extra charge
# + F&B = 200
# TOTAL = 150 + 50 + 200 = 400
```

#### **Session Methods**
```python
# Timing
session.get_elapsed_minutes()        # Minutes used (excl. pauses)

# Billing (All return Decimal)
session.calculate_room_charge()      # Base charge
session.calculate_extra_time_charge() # Extra time premium
session.recalculate_total()          # Recalc: room + extra + F&B

# Session Management
session.pause_session()              # Pause active session
session.resume_session()             # Resume paused session
session.add_extra_time(minutes)      # Add time mid-session
session.complete_session()           # Finalize & close
```

#### **Views**
- **start_session**: Create new session, set room to Active
- **manage_session**: Pause/resume, add time (POST-based actions)
- **checkout_session**: Complete session, calculate charges, create SaleTransaction

#### **Admin Interface**
- Room management (status, pricing, capacity)
- RoomSession admin with full billing details
- BookingRequest, RoomOrder, RoomOrderItem admin panels

#### **Multi-Tenant Safety**
- All sessions filtered by `request.outlet`
- Checkout checks `session.outlet == request.outlet`
- Cascade deletes respect outlet isolation

---

## Key Database Models & Relations
```
Outlet (1) ─────────→ (∞) Room
  ├─────────→ (∞) RoomSession
  ├─────────→ (∞) Product
  ├─────────→ (∞) SaleTransaction
  └─────────→ (∞) Customer

Room (1) ────────────→ (∞) RoomSession
RoomSession (1) ────→ (∞) RoomOrder
RoomOrder (1) ───────→ (∞) RoomOrderItem ──→ Product
```

---

## API Routes (Karaoke)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/karaoke/session/start/` | Session creation form |
| POST | `/karaoke/session/start/` | Create new session |
| GET | `/karaoke/session/manage/<id>/` | Manage active session |
| POST | `/karaoke/session/manage/<id>/` | Pause/resume/add time |
| GET | `/karaoke/session/checkout/<id>/` | Checkout form |
| POST | `/karaoke/session/checkout/<id>/` | Finalize session & payment |

---

## Recent Changes (2025-12-23)
- **Phase 3 Karaoke Module**: Complete backend implementation
  - Room model with status lifecycle
  - RoomSession with comprehensive billing logic
  - Duration-based pricing: (minutes / 60) × hourly_rate
  - Session pause/resume tracking
  - Extra time management
  - Admin interface for room & session management
  - Multi-tenant outlet isolation on all models
  - Database migrations: 0012_delete_roomsession_roomsession_and_more

---

## Next Phases

1. **Karaoke Frontend** (Priority)
   - Session dashboard with real-time progress bars
   - Tablet interface for in-room orders
   - Staff session management interface

2. **Inventory Intelligence**
   - Low stock alert system
   - Multi-outlet stock transfers

3. **HR & Payroll** (Complex)
   - Three payment types: P (Fixed), C (Hourly), D (Daily)
   - Attendance tracking with GPS

4. **Financial Intelligence**
   - P&L reports (Revenue - Expenses)
   - Outlet performance dashboards
