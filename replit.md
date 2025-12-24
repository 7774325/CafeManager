# CafeManager - Enterprise Café & Karaoke Management System

## Overview
Multi-tenant, enterprise-grade platform for managing independent hospitality outlets. Designed as "Loyverse+" with deep karaoke integration, real-time POS, inventory, and HR/Payroll.

---

## PHASES COMPLETED

### Phase 1: Multi-Tenant Architecture ✅
- Outlet Middleware: `request.outlet` on every request
- All models have outlet FK for complete data isolation

### Phase 2: POS System ✅
- Interactive product grid with real-time cart
- Checkout with automatic stock deduction
- Customer profiles with visit tracking
- **Endpoints**: `/pos/`, `/api/pos/submit/`

### Phase 3: Karaoke Module Backend ✅
- Room model with status lifecycle
- RoomSession with billing: `(minutes / 60) × hourly_rate`
- Session control: pause/resume, extra time

### Phase 4: Inventory Management ✅
- InventoryLog model tracking all stock changes
- Real-time stock deduction in POS
- Low-stock dashboard with configurable threshold
- **Route**: `/stock/low/`

### Phase 5: HR & Payroll ✅

#### **Employee Profiles** (Multi-Tenant)
- Linked to `outlet` FK for outlet isolation
- Payment types: **P** (Permanent), **C** (Commission), **D** (Daily-Rated)
- Fields: name, role, phone, email, payment_type, base_salary, commission_rate
- Admin: Filter by outlet, payment_type, is_active

#### **Attendance Tracking**
- Check-in/Check-out system with automatic hour calculation
- Indexed by outlet + date, employee + date
- Fields: date, check_in_time, check_out_time, hours_worked
- Models: `Attendance(employee, outlet, date, check_in_time, check_out_time, hours_worked)`
- Method: `calculate_hours_worked()` - auto-calculates based on check-in/out

#### **Three Payment Structures**
```python
# P (Permanent): Fixed monthly salary
base_amount = employee.base_salary
commission_amount = 0

# D (Daily-Rated): Daily rate × working days
base_amount = employee.base_salary × working_days
commission_amount = 0

# C (Commission-Based): Min salary + % of outlet sales
base_amount = employee.base_salary (minimum)
commission_amount = (total_outlet_sales × commission_rate / 100)
```

#### **Payroll Model**
Fields:
- `employee`, `outlet`, `year`, `month`
- `total_hours_worked`, `base_amount`, `commission_amount`, `total_earnings`
- `deductions`, `net_pay`
- `status`: Draft → Calculated → Approved → Paid
- Method: `calculate_payroll()` - calculates based on payment type + attendance

#### **Management Views**
1. **Attendance Report** (`/attendance/report/`)
   - Filter by year/month
   - Shows all employee check-in/out times for the month
   - Hours worked calculated automatically
   - Filter button to recalculate payroll

2. **Payroll Report** (`/payroll/report/`)
   - Shows monthly payroll for all employees
   - Breaks down: Base + Commission + Earnings
   - Shows deductions and net pay
   - Status tracking

3. **Check-In/Check-Out** (Quick Links)
   - `/attendance/check-in/` - Creates attendance record + logs check-in time
   - `/attendance/check-out/` - Calculates hours, logs check-out time
   - Auto-redirect to dashboard with success messages

#### **Payroll Calculation**
- Route: `/payroll/calculate/?month=X&year=Y`
- Calculates for ALL active employees at outlet
- Uses Attendance data for daily-rated employees
- Uses SaleTransaction data for commission-based employees
- Auto-creates Payroll records in Draft status
- Calls `calculate_payroll()` to compute amounts

#### **Multi-Tenant Isolation**
- Employee FK to outlet (cannot access other outlet's employees)
- Attendance filtered by `request.outlet`
- Payroll filtered by `request.outlet`
- All views use `get_user_outlet(request.user)`

#### **Admin Interface**
- EmployeeAdmin: Show payment_type, base_salary, is_active
- AttendanceAdmin: Sortable by date, searchable by employee
- PayrollAdmin: Filterable by status, year, month; read-only calculated fields

#### **Database Migration**
- Migration 0024: Added Employee payment fields, created Attendance & Payroll models

---

## API Routes

### HR & Payroll
| Route | Method | Purpose |
|-------|--------|---------|
| `/attendance/check-in/` | GET | Record check-in time |
| `/attendance/check-out/` | GET | Record check-out time |
| `/attendance/report/` | GET | View attendance for month |
| `/payroll/calculate/` | GET | Calculate payroll for month |
| `/payroll/report/` | GET | View payroll results |

### Inventory
| Route | Method | Purpose |
|-------|--------|---------|
| `/stock/low/` | GET | Low stock dashboard |

### POS
| Route | Method | Purpose |
|-------|--------|---------|
| `/pos/` | GET | POS interface |
| `/api/pos/submit/` | POST | Checkout |

---

## Recent Changes (2025-12-24)

**Phase 5: HR & Payroll System**
- Expanded Employee model: payment_type, base_salary, commission_rate, is_active
- Created Attendance model: check-in/check-out with auto hour calculation
- Created Payroll model: monthly calculations for 3 payment types
- Implemented payroll calculation logic:
  - Permanent: Fixed base_salary
  - Daily-Rated: base_salary × working_days
  - Commission-Based: base_salary + (sales × commission_rate)
- Built management views: attendance report, payroll report, check-in/check-out
- Created lavender-themed UI for reports
- Admin interface for attendance & payroll tracking
- Migration 0024 applied successfully

---

## Technology Stack
- Framework: Django 5.2 + REST Framework
- Server: Daphne (ASGI, WebSocket-ready)
- Database: SQLite (dev), PostgreSQL (production)
- Frontend: Bootstrap 5 + vanilla JS
- UI: Lavender & black gradient design

---

## Next Phases

1. **GPS Attendance** (Future)
   - Location-based check-in
   - Distance validation

2. **Advanced Payroll**
   - Deduction management
   - Tax calculations
   - Bank transfer integration

3. **Financial Intelligence**
   - P&L reports
   - Outlet performance dashboards
   - Year-over-year analysis
